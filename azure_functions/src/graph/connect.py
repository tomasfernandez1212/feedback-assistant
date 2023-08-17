import logging
import time
from typing import List, Type, Dict, Any
from enum import Enum
from src.data import GraphNode, ListGraphNodes, LABEL_TO_CLASS, GraphNodeVar

from src.data.reviews import Review
import os, sys, asyncio, json

from gremlin_python.driver import client, serializer  # type: ignore
from gremlin_python.driver.protocol import GremlinServerError  # type: ignore

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class GraphConnection:
    def __init__(self, strong_consistency: bool = False) -> None:
        self.strong_consistency = strong_consistency

        preprend = "EVENTUAL_GRAPH"
        if strong_consistency:
            preprend = "STRONG_GRAPH"

        self.host_name = os.environ.get(f"{preprend}_HOST_NAME")
        self.db_name = os.environ.get(f"{preprend}_DB_NAME")
        self.graph_name = os.environ.get(f"{preprend}_GRAPH_NAME")
        DB_KEY = os.environ.get(f"{preprend}_DB_KEY")

        if DB_KEY is None:
            raise Exception(f"{preprend}_DB_KEY is not set")

        self.gremlin_client = client.Client(
            f"wss://{self.host_name}.gremlin.cosmos.azure.com:443/",
            "g",
            username=f"/dbs/{self.db_name}/colls/{self.graph_name}",
            password=DB_KEY,
            message_serializer=serializer.GraphSONSerializersV2d0(),
        )

        self.graph_label_to_class = LABEL_TO_CLASS

    def close(self):
        self.gremlin_client.close()

    def reset_graph(self, confirm_graph_name: str):
        if confirm_graph_name != self.graph_name:
            raise Exception("Graph name does not match")
        query = "g.V().drop()"
        result = self.submit_query(query)  # type: ignore
        logging.info(f"Reset graph {self.graph_name}.")

    def delete_node(self, id: str):
        query = f"g.V('{id}').drop()"
        result = self.submit_query(query)  # type: ignore
        if len(result) != 1:
            raise Exception(f"Error deleting node {id}.")
        logging.info(f"Deleted node {id}.")

    def check_if_node_exists(self, id: str) -> bool:
        query = f"g.V('{id}')"
        result = self.submit_query(query)  # type: ignore
        if len(result) == 0:
            node_exists = False
        else:
            node_exists = True
        return node_exists  # type: ignore

    def get_node_as_str(self, node_id: str) -> str:
        query = f"g.V('{node_id}')"
        result = self.submit_query(query)  # type: ignore
        if len(result) != 1:
            raise Exception(f"Found {len(result)} nodes with ID {node_id}.")
        result = json.dumps(result[0])  # type: ignore
        return result

    def str_to_object(self, node_str: str, type: Type[GraphNodeVar]) -> GraphNodeVar:
        node_json = json.loads(node_str)
        node_unpacked = node_json["properties"]
        for key, list_of_json in node_unpacked.items():
            node_unpacked[key] = list_of_json[0]["value"]
        node_unpacked["id"] = node_json["id"]
        node = type.model_validate(node_unpacked)
        return node

    def get_node(self, id: str, type: Type[GraphNodeVar]) -> GraphNodeVar:
        node_str = self.get_node_as_str(id)
        node = self.str_to_object(node_str, type)
        return node

    def get_all_nodes_by_type(self, type: Type[GraphNodeVar]) -> List[GraphNodeVar]:
        query = f"g.V().hasLabel('{type.__name__}')"
        result = self.submit_query(query)  # type: ignore
        nodes = []
        for node_dict in result:  # type: ignore
            node_str = json.dumps(node_dict)
            node = self.str_to_object(node_str, type)
            nodes.append(node)  # type: ignore
        return nodes  # type: ignore

    def add_properties_to_query(
        self, query: str, node: GraphNode, updating: bool = False
    ) -> str:
        model_dict = node.model_dump()

        for key, value in model_dict.items():
            if updating and key == "id":
                continue  # Don't update the ID
            if isinstance(value, Enum):
                value = value.value  # Unpack the enum's value
            if isinstance(value, str):
                escaped_value = value.replace("'", "\\'")  # Escape single quotes
                query += f".property('{key}', '{escaped_value}')"  # Quotes to indicate string
            elif isinstance(value, list):
                escaped_value = value.__str__().replace(
                    "'", "\\'"
                )  # Escape single quotes in the list as string
                query += f".property('{key}', '{escaped_value}')"  # Treat list as string to store as single property

            else:
                query += f".property('{key}', {value})"  # Assume it's a number

        # Add Partition Key - We use the ID since it is a random UUID
        if not updating:
            query += f".property('pk', '{model_dict['id']}')"

        return query

    def add_node(self, node: GraphNode, skip_existing: bool = True):
        label = type(node).__name__

        logging.info(f"Adding {node.id} of type {label}.")

        if skip_existing:
            if self.check_if_node_exists(node.id):
                logging.info(f"Skipping adding {node.id} because it already exists")
                return

        query = f"g.addV('{label}')"
        query = self.add_properties_to_query(query, node)

        result = self.submit_query(query)  # type: ignore
        if len(result) == 0:
            raise Exception(f"Error adding node {node.id} of type {label}.")

        logging.info(f"Added {node.id} of type {label}.")

    def add_nodes(self, nodes: ListGraphNodes):
        for node in nodes:
            self.add_node(node)

    def add_edges(
        self,
        from_nodes: ListGraphNodes,
        to_nodes: ListGraphNodes,
        edge_label: str,
    ):
        """
        Adds edges between nodes. Assumes that the nodes already exist in the graph.
        """

        if len(from_nodes) == 0 or len(to_nodes) == 0:
            return

        for from_node in from_nodes:
            for to_node in to_nodes:
                self.add_edge(from_node, to_node, edge_label)

    def add_edge(self, from_node: GraphNode, to_node: GraphNode, edge_label: str):
        """
        Add edge between two nodes. Assumes that the nodes already exist in the graph.

        Due to distributed nature of CosmosDB, there is eventual consistency but it is possible that the nodes do not exist in the graph yet.

        For this reason we retry the query if it returns an empty list.
        """

        edge_exists = self.check_if_edge_exists(from_node, to_node, edge_label)
        if edge_exists:
            logging.info(
                f"Edge from {from_node.id} to {to_node.id} of type {edge_label} already exists."
            )
            return

        MAX_RETRIES = 3
        RETRY_DELAY = 0.2  # time to wait between retries, in seconds

        for attempt in range(MAX_RETRIES):
            try:
                query = f"g.V('{from_node.id}').addE('{edge_label}').to(g.V('{to_node.id}'))"
                logging.info(f"Attempt: {attempt + 1} at adding edge.")
                result = self.submit_query(query)  # type: ignore
                if len(result) == 1:  # type: ignore
                    logging.info("Successfully added edge.")
                    break  # successfully added this edge
            except:
                if attempt < MAX_RETRIES - 1:  # i.e. not the last attempt
                    time.sleep(RETRY_DELAY)  # wait before next attempt
                else:
                    logging.warning(f"Failed to add edge after {MAX_RETRIES} attempts.")

    def update_node(self, node: GraphNode):
        """
        Updates a node in the graph. Assumes that the node already exists in the graph.
        """
        if not self.check_if_node_exists(node.id):
            raise Exception(f"Node {node.id} does not exist.")

        query = f"g.V('{node.id}')"
        query = self.add_properties_to_query(query, node, updating=True)

        result = self.submit_query(query)  # type: ignore

        if len(result) != 1:  # type: ignore
            raise Exception(
                f"Error updating node {node.id}. Expected 1 result, got {len(result)}."  # type: ignore
            )

    def traverse(self, node: GraphNode, edge_label: str) -> List[Review]:
        query = f"g.V('{node.id}').out('{edge_label}')"
        list_of_node_dicts = self.submit_query(query)  # type: ignore
        list_of_nodes = []
        for node_dict in list_of_node_dicts:  # type: ignore
            expected_type = self.graph_label_to_class[node_dict["label"]]  # type: ignore
            list_of_nodes.append(  # type: ignore
                self.str_to_object(json.dumps(node_dict), expected_type)
            )
        return list_of_nodes  # type: ignore

    def check_if_edge_exists(
        self, from_node: GraphNode, to_node: GraphNode, edge_label: str
    ) -> bool:
        query = f"g.V('{from_node.id}').outE('{edge_label}').where(inV().hasId('{to_node.id}'))"
        result = self.submit_query(query)  # type: ignore
        return len(result) > 0  # type: ignore

    def submit_query(self, query: str) -> List[Dict[str, Any]]:
        result_set = self.gremlin_client.submit(query)  # type: ignore
        future = result_set.all()  # type: ignore
        result = future.result()  # type: ignore
        return result  # type: ignore

import logging
import time
from typing import List, TypeVar, Type, Optional
from enum import Enum
from src.graph.data import NodeType, ListNodesType, LABEL_TO_CLASS

from src.graph.data.reviews import Review
from src.graph.data.feedbackItems import FeedbackItem
import os, sys, asyncio, json

from gremlin_python.driver import client, serializer  # type: ignore
from gremlin_python.driver.protocol import GremlinServerError  # type: ignore

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

NodeTypeVar = TypeVar("NodeTypeVar", bound=NodeType)


class GraphConnection:
    def __init__(self, strong_consistency: bool = False) -> None:
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
        callback = self.gremlin_client.submit(query)  # type: ignore
        callback.one()  # type: ignore

    def check_if_node_exists(self, id: str) -> bool:
        query = f"g.V('{id}')"
        callback = self.gremlin_client.submit_async(query)  # type: ignore
        one: list = callback.result().one()  # type: ignore
        result = len(one)  # type: ignore
        node_exists: bool = result >= 1  # type: ignore
        return node_exists  # type: ignore

    def get_node_as_str(self, node_id: str) -> str:
        query = f"g.V('{node_id}')"
        callback = self.gremlin_client.submit_async(query)  # type: ignore
        result = json.dumps(callback.result().one()[0])  # type: ignore
        return result

    def str_to_object(self, node_str: str) -> NodeType:
        label = json.loads(node_str)["label"]
        model_class = self.graph_label_to_class[label]
        node_json = json.loads(node_str)
        node_unpacked = node_json["properties"]
        for key, list_of_json in node_unpacked.items():
            node_unpacked[key] = list_of_json[0]["value"]
        node_unpacked["id"] = node_json["id"]
        node = model_class.model_validate(node_unpacked)
        return node

    def get_node(self, id: str) -> NodeType:
        node_str = self.get_node_as_str(id)
        node = self.str_to_object(node_str)
        return node

    def get_all_nodes_by_type(self, type: Type[NodeTypeVar]) -> List[NodeTypeVar]:
        query = f"g.V().hasLabel('{type.__name__}')"
        callback = self.gremlin_client.submit_async(query)  # type: ignore
        result = callback.result().all().result()  # type: ignore
        nodes = []
        for node_dict in result:  # type: ignore
            node_str = json.dumps(node_dict)
            node = self.str_to_object(node_str)
            nodes.append(node)  # type: ignore
        return nodes  # type: ignore

    def add_node(self, node: NodeType, skip_existing: bool = True):
        label = type(node).__name__

        logging.info(f"Adding {node.id} of type {label}.")

        if skip_existing:
            if self.check_if_node_exists(node.id):
                logging.info(f"Skipping adding {node.id} because it already exists")
                return

        query = f"g.addV('{label}')"

        for key, value in node.model_dump().items():
            if isinstance(value, str):
                query += f".property('{key}', '{value}')"  # Quotes to indicate string
            elif isinstance(value, list):
                query += f".property('{key}', '{value.__str__()}')"  # Treat list as string to store as single property
            elif isinstance(value, Enum):
                query += f".property('{key}', {value.value})"  # Unpack the enum's value
            else:
                query += f".property('{key}', {value})"  # Assume it's a number

        query += ".property('pk', 'pk')"

        callback = self.gremlin_client.submit(query)  # type: ignore
        result_set = callback.all()  # type: ignore

        logging.info(f"Added {node.id} of type {label}.")

    def add_nodes(self, nodes: ListNodesType):
        for node in nodes:
            self.add_node(node)

    def add_edges(
        self,
        from_nodes: ListNodesType,
        to_nodes: ListNodesType,
        edge_label: str,
    ):
        """
        Adds edges between nodes. Assumes that the nodes already exist in the graph.

        Due to distributed nature of CosmosDB, there is eventual consistency but it is possible that the nodes do not exist in the graph yet.

        For this reason we retry the query if it returns an empty list.
        """

        MAX_RETRIES = 3
        RETRY_DELAY = 0.2  # time to wait between retries, in seconds

        for from_node in from_nodes:
            for to_node in to_nodes:
                for attempt in range(MAX_RETRIES):
                    try:
                        query = f"g.V('{from_node.id}').addE('{edge_label}').to(g.V('{to_node.id}'))"
                        logging.info(f"Attempt: {attempt + 1} at adding edge.")
                        callback = self.gremlin_client.submit(query)  # type: ignore
                        edge = callback.one()  # type: ignore
                        if len(edge) > 0:  # type: ignore
                            logging.info("Successfully added edge.")
                            break  # successfully added this edge
                    except:
                        if attempt < MAX_RETRIES - 1:  # i.e. not the last attempt
                            time.sleep(RETRY_DELAY)  # wait before next attempt
                        else:
                            raise  # re-raise the last exception

    def add_feedback_item(
        self, feedback_item: FeedbackItem, constituted_by: Optional[Review] = None
    ):
        """
        Adds feedback item as a node, but also adds edge to node it is constituted by.
        For now, constituted by can only be a review, but in the future it could be a messaging thread.

        Constituted by should generally be provided, but might be optional for particular testing scenarios.
        """

        self.add_node(feedback_item)

        if constituted_by:
            self.add_edges([feedback_item], [constituted_by], "constituted_by")

    def traverse(self, node: NodeType, edge_label: str) -> List[Review]:
        query = f"g.V('{node.id}').out('{edge_label}')"
        callback = self.gremlin_client.submit(query)  # type: ignore
        future = callback.all()  # type: ignore
        list_of_node_dicts = future.result()  # type: ignore
        list_of_nodes = []
        for node_dict in list_of_node_dicts:  # type: ignore
            list_of_nodes.append(self.str_to_object(json.dumps(node_dict)))  # type: ignore
        return list_of_nodes  # type: ignore

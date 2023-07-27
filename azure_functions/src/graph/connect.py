import logging
from enum import Enum
from typing import Union

from src.graph.data.reviews import Review
from src.graph.data.feedbackItems import FeedbackItem
import os, sys, asyncio, json

from gremlin_python.driver import client, serializer  # type: ignore
from gremlin_python.driver.protocol import GremlinServerError  # type: ignore

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class GraphConnection:
    def __init__(self) -> None:
        AZURE_COSMOS_HOST_NAME = os.environ.get("AZURE_COSMOS_HOST_NAME")
        AZURE_COSMOS_DB_NAME = os.environ.get("AZURE_COSMOS_DB_NAME")
        AZURE_COSMOS_GRAPH_NAME = os.environ.get("AZURE_COSMOS_GRAPH_NAME")
        AZURE_COSMOS_DB_KEY = os.environ.get("AZURE_COSMOS_DB_KEY")

        if AZURE_COSMOS_DB_KEY is None:
            raise Exception("AZURE_COSMOS_DB_KEY is not set")

        self.gremlin_client = client.Client(
            f"wss://{AZURE_COSMOS_HOST_NAME}.gremlin.cosmos.azure.com:443/",
            "g",
            username=f"/dbs/{AZURE_COSMOS_DB_NAME}/colls/{AZURE_COSMOS_GRAPH_NAME}",
            password=AZURE_COSMOS_DB_KEY,
            message_serializer=serializer.GraphSONSerializersV2d0(),
        )

        self.graph_label_to_class = {
            "Review": Review,
            "FeedbackItem": FeedbackItem,
        }

    def close(self):
        self.gremlin_client.close()

    def reset_graph(self, confirm_graph_name: str):
        if confirm_graph_name != os.environ["AZURE_COSMOS_GRAPH_NAME"]:
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

    def str_to_object(self, node_str: str) -> Union[Review, FeedbackItem]:
        label = json.loads(node_str)["label"]
        model_class = self.graph_label_to_class[label]
        node_json = json.loads(node_str)
        node_unpacked = node_json["properties"]
        for key, list_of_json in node_unpacked.items():
            node_unpacked[key] = list_of_json[0]["value"]
        node = model_class.model_validate(node_unpacked)
        return node

    def get_node(self, id: str) -> Union[Review, FeedbackItem]:
        node_str = self.get_node_as_str(id)
        node = self.str_to_object(node_str)
        return node

    def add_node(self, node: Union[Review, FeedbackItem], skip_existing: bool = True):
        if skip_existing:
            if self.check_if_node_exists(node.id):
                logging.info(f"Skipping adding {node.id} because it already exists")
                return

        label = type(node).__name__

        query = f"g.addV('{label}')"

        for key, value in node.model_dump().items():
            if isinstance(value, str):
                query += f".property('{key}', '{value}')"  # Escape the string
            elif isinstance(value, Enum):
                query += f".property('{key}', {value.value})"  # Unpack the enum's value
            else:
                query += f".property('{key}', {value})"  # Assume it's a number

        query += ".property('pk', 'pk')"

        callback = self.gremlin_client.submit(query)  # type: ignore
        callback.one()  # type: ignore

    def add_nodes(self, nodes: Union[list[Review], list[FeedbackItem]]):
        for node in nodes:
            self.add_node(node)

    def add_edge(
        self,
        from_node: Union[Review, FeedbackItem],
        to_node: Union[Review, FeedbackItem],
        edge_label: str,
    ):
        query = f"g.V('{from_node.id}').addE('{edge_label}').to(g.V('{to_node.id}'))"
        callback = self.gremlin_client.submit(query)
        callback.one()

    def traverse(self, node: Union[Review, FeedbackItem], edge_label: str):
        query = f"g.V('{node.id}').out('{edge_label}')"
        callback = self.gremlin_client.submit(query)
        results = callback.all()
        return results

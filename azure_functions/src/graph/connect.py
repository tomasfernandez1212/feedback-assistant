import logging
from src.graph.data.reviews import Review
from src.graph.data.feedbackItems import FeedbackItem
import os, sys, asyncio, json

from gremlin_python.driver import client, serializer  # type: ignore

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

    def get_node_by_id_as_str(self, node_id: str) -> str:
        query = f"g.V('{node_id}')"
        callback = self.gremlin_client.submitAsync(query)  # type: ignore
        result = json.dumps(callback.result().one()[0])  # type: ignore
        return result

    def check_if_node_exists(
        self, node_label: str, node_id_value: str, node_id_name: str = "id"
    ) -> bool:
        query = (
            f"g.V().has('{node_label}', '{node_id_name}', '{node_id_value}').Count()"
        )
        callback = self.gremlin_client.submitAsync(query)  # type: ignore
        result: int = callback.result().one()[0]  # type: ignore
        node_exists: bool = result >= 1  # type: ignore
        return node_exists  # type: ignore

    def add_review(self, review: Review) -> None:
        node_exists = self.check_if_node_exists("review", review.review_id)

        if node_exists:
            logging.info(f"Review {review.review_id} already exists in graph")
            return

        review_text = review.text.replace("\n", "\\n").replace("'", "\\'")
        query = f"g.addV('review').property('id', '{review.review_id}').property('date', '{review.date}').property('rating', '{review.rating.value}').property('text', '{review_text}').property('source', '{review.source.name}').property('source_review_id', '{review.source_review_id}').property('pk', 'pk')"
        callback = self.gremlin_client.submitAsync(query)  # type: ignore

    def add_reviews(self, reviews: list[Review]) -> None:
        for review in reviews:
            self.add_review(review)

    def get_review(self, id: str) -> Review:
        node_str = self.get_node_by_id_as_str(id)
        review = Review.model_validate_json(node_str)
        return review

    def add_feedback_item(self, feedback_item: FeedbackItem) -> None:
        query = f"g.addV('feedbackItem').property('timestamp', '{feedback_item.timestamp}').property('satisfaction_score', '{feedback_item.satisfaction_score}').property('pk', 'pk')"
        callback = self.gremlin_client.submitAsync(query)  # type: ignore

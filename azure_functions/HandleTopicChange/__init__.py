import logging

import azure.functions as func
from src.storage import Storage
from src.data.dataPoint import DataPoint
from src.data.topics import Topic
from src.llm.connections import infer_topic_to_data_points_connections


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting Topic with ID: {id}")
        topic = storage.get_node(id, Topic)

        logging.info("Infer related Data Points")
        existing_data_points, scores = storage.search_semantically(  # type: ignore
            search_for=DataPoint, from_text=topic.text, top_k=10, min_score=0.0
        )
        related_data_points = infer_topic_to_data_points_connections(
            topic, existing_data_points
        )
        storage.add_topic_to_data_points_edges(topic, related_data_points)
        logging.info(
            f"Topic: \n\n {topic.text} \n\nContains Data Points: {related_data_points}\n\n"
        )

        return func.HttpResponse("Done")

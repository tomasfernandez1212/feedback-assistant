import logging, json

import azure.functions as func
from src.storage import Storage
from src.data.dataPoint import DataPoint
from src.data.topics import Topic
from src.data.actionItems import ActionItem
from src.llm.connections import (
    infer_data_point_to_action_items_connections,
    infer_data_point_to_topics_connections,
)


def main(msg: func.ServiceBusMessage) -> None:
    logging.info("INIT: Unpacking Request Body")
    req_body = json.loads(msg.get_body())
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting DataPoint with ID: {id}")
        data_point = storage.get_node(id, DataPoint)

        logging.info("Infer related Action Items")
        existing_action_items, scores = storage.search_semantically(  # type: ignore
            search_for=ActionItem, from_text=data_point.text, top_k=10, min_score=0.0
        )
        related_action_items = infer_data_point_to_action_items_connections(
            data_point, existing_action_items
        )
        storage.add_data_point_to_action_items_edges(data_point, related_action_items)
        logging.info(
            f"Data Point: \n\n {data_point.text} \n\nAddressed by Action Items: {related_action_items}\n\n"
        )

        logging.info("Infer related Topics")
        existing_topics, scores = storage.search_semantically(  # type: ignore
            search_for=Topic, from_text=data_point.text, top_k=10, min_score=0.0
        )
        related_topics = infer_data_point_to_topics_connections(
            data_point, existing_topics
        )
        storage.add_data_point_to_topics_edges(data_point, related_topics)
        logging.info(
            f"Data Point: \n\n {data_point.text} \n\nBelongs to Topics: {related_topics}\n\n"
        )

    logging.info("DONE: Finished processing.")

import logging

import azure.functions as func
from src.storage import Storage
from src.data.dataPoint import DataPoint
from src.data.topics import Topic


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting DataPoint with ID: {id}")
        data_point = storage.get_node(id, DataPoint)

        logging.info("Get related topics")
        existing_topics = storage.search_semantically(
            search_for=Topic, from_text=data_point.text, top_k=10, min_score=0.0
        )
        for existing_topic in existing_topics:
            print(existing_topic)

        return func.HttpResponse("Done")

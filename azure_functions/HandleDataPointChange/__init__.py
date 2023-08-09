import logging

import azure.functions as func
from src.storage import Storage
from src.data.dataPoint import DataPoint
from src.openai import OpenAIInterface


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting DataPoint with ID: {id}")
        data_point = storage.get_node(id, DataPoint)

        logging.info("Get related topics")
        openai_interface = OpenAIInterface()
        data_point_embedding = openai_interface.get_embedding(data_point.interpretation)
        existing_topics = storage.search_with_embedding(DataPoint, data_point_embedding)
        for existing_topic in existing_topics:
            print(existing_topic)

        return func.HttpResponse("Done")

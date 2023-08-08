import logging

import azure.functions as func
from src.storage import Storage
from src.data.dataPoint import DataPoint


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting DataPoint with ID: {id}")
        data_point = storage.get_node(id, DataPoint)

        logging.info(f"Got DataPoint: {data_point}")
        return func.HttpResponse("Done")

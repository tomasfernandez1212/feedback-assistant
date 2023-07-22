import logging

import azure.functions as func
from src.graph.connect import GraphConnection


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Request received.")

    req_body = req.get_json()

    logging.info(f"Request body: {req_body}")

    id: str = req_body.get("id")

    logging.info(f"Handling Review Change for ID: {id}")

    return func.HttpResponse(f"Handling Review Change for ID: {id}")

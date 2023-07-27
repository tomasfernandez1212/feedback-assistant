import logging

import azure.functions as func

from src.graph.connect import GraphConnection

from src.openai import OpenAIInterface


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    logging.info(f"Getting FeedbackItem with ID: {id}")
    graph = GraphConnection()
    feedback_item = graph.get_node(id)

    logging.info("Getting Review")
    result = graph.traverse(feedback_item, "constituted_by")
    review = result[0]

    logging.info("Getting Topic Tags")
    openai_interface = OpenAIInterface()
    list_of_tags = openai_interface.get_list_of_topics(review.text)

    return func.HttpResponse(f"Hanlded FeedbackItem Change.", status_code=200)

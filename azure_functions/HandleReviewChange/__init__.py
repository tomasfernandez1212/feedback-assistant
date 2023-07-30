import logging

import azure.functions as func

from src.graph.connect import GraphConnection
from src.graph.data.reviews import Review
from src.graph.data.feedbackItems import FeedbackItem

from src.openai import OpenAIInterface


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    logging.info(f"Getting Review with ID: {id}")
    graph = GraphConnection()
    review = graph.get_node(id, Review)
    if type(review) != Review:
        graph.close()
        return func.HttpResponse(
            f"Node with ID: {id} is not a review.", status_code=404
        )

    logging.info("Getting Satisfaction Score")
    openai_interface = OpenAIInterface()
    score = openai_interface.get_satisfaction_score(review.text)

    logging.info("Creating Feedback Item")
    feedback_item = FeedbackItem(
        satisfaction_score=score,
        timestamp=123,  # TODO: Get timestamp from review
    )

    logging.info("Adding Feedback Item to Graph")
    graph.add_feedback_item(feedback_item, constituted_by=review)

    logging.info("Closing Graph Connection")
    graph.close()

    return func.HttpResponse("Handled Review Change", status_code=200)

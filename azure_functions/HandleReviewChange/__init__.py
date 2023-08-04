import logging

import azure.functions as func

from src.storage import Storage
from src.data.reviews import Review
from src.data.feedbackItems import FeedbackItem


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting Review with ID: {id}")
        review = storage.get_node(id, Review)
        if type(review) != Review:
            return func.HttpResponse(
                f"Node with ID: {id} is not a review.", status_code=404
            )

        logging.info("Creating Feedback Item")
        feedback_item = FeedbackItem()

        logging.info("Adding Feedback Item to Graph")
        storage.add_feedback_item(feedback_item, constituted_by=review)

        logging.info("Closing Graph Connection")

        return func.HttpResponse("Handled Review Change", status_code=200)

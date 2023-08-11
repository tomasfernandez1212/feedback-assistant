import logging

import azure.functions as func

from src.data.feedbackItems import FeedbackItem
from src.data.actionItems import ActionItem
from src.data.topics import Topic
from src.storage import Storage

from src.llm.data_points import generate_data_points
from src.llm.action_items import generate_action_items
from src.llm.topics import generate_topics
from src.llm.scores import score_data_point, ScoreType

from typing import List


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("INIT: Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"INIT: Getting FeedbackItem with ID: {id}")
        feedback_item = storage.get_node(id, FeedbackItem)

        logging.info("DATAPOINTS: Generating Data Points")
        data_points = generate_data_points(feedback_item.text)

        for data_point in data_points:
            logging.info("DATAPOINTS: Scoring Data Point")
            scores = score_data_point(
                data_point.text,
                feedback_item.text,
                [
                    ScoreType.SATISFACTION,
                    ScoreType.SPECIFICITY,
                    ScoreType.BUSINESS_IMPACT,
                ],
            )

            logging.info("DATAPOINTS: Adding to Storage")
            storage.add_data_point_for_feedback_item(data_point, feedback_item)
            for score in scores:
                storage.add_score(data_point, score)

        logging.info(
            "ACTIONITEMS: Getting new action items for feedback item, embedding, and adding to storage"
        )
        existing_action_items: List[ActionItem] = []  # Get from vectorsearch
        new_action_items = generate_action_items(
            feedback_item.text, data_points, existing_action_items
        )
        for new_action_item in new_action_items:
            storage.add_action_item(new_action_item)

        logging.info("TOPICS: Getting new topics for feedback item")
        existing_topics: List[Topic] = []  # Get from vectorsearch
        new_topics = generate_topics(feedback_item.text, data_points, existing_topics)
        for new_topic in new_topics:
            storage.add_topic(new_topic)

        return func.HttpResponse(f"Hanlded FeedbackItem Change.", status_code=200)

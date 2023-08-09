import logging

import azure.functions as func

from src.data.dataPoint import DataPoint
from src.data.feedbackItems import FeedbackItem
from src.data.actionItems import ActionItem
from src.data.topics import Topic
from src.storage import Storage

from src.openai import OpenAIInterface, ScoreType

from typing import List


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("INIT: Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"INIT: Getting FeedbackItem with ID: {id}")
        feedback_item = storage.get_node(id, FeedbackItem)

        logging.info("DATAPOINTS: Getting Text For Data Points")
        openai_interface = OpenAIInterface()
        data_points_text = openai_interface.get_data_points_text(feedback_item.text)
        data_points: List[DataPoint] = []

        for data_point_text in data_points_text:
            logging.info("DATAPOINTS: Creating Data Point")
            data_point = DataPoint(interpretation=data_point_text)
            data_points.append(data_point)

            logging.info("DATAPOINTS: Scoring Data Point")
            scores = openai_interface.score_data_point(
                data_point_text,
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

            logging.info("DATAPOINTS: Embedding Data Point and Adding to Storage")
            data_point_embedding = openai_interface.get_embedding(
                data_point.interpretation
            )
            storage.add_embedding(data_point.id, DataPoint, data_point_embedding)

        logging.info(
            "ACTIONITEMS: Getting new action items for feedback item, embedding, and adding to storage"
        )
        existing_action_items: List[ActionItem] = []  # Get from vectorsearch
        new_action_items = openai_interface.get_new_action_items(
            feedback_item.text, data_points, existing_action_items
        )
        for new_action_item in new_action_items:
            storage.add_action_item(new_action_item)
            action_item_embedding = openai_interface.get_embedding(new_action_item.text)
            storage.add_embedding(new_action_item.id, ActionItem, action_item_embedding)

        logging.info("TOPICS: Getting new topics for feedback item")
        existing_topics: List[Topic] = []  # Get from vectorsearch
        new_topics = openai_interface.get_new_topics(
            feedback_item.text, data_points, existing_topics
        )
        for new_topic in new_topics:
            storage.add_topic(new_topic)
            topic_embedding = openai_interface.get_embedding(new_topic.name)
            storage.add_embedding(new_topic.id, Topic, topic_embedding)

        return func.HttpResponse(f"Hanlded FeedbackItem Change.", status_code=200)

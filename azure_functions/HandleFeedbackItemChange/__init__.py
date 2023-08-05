import logging
import time

import azure.functions as func

from src.data.dataPoint import DataPoint
from src.data.feedbackItems import FeedbackItem
from src.data.actionItems import ActionItem
from src.storage import Storage

from src.openai import OpenAIInterface, ScoreType

from typing import List


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting FeedbackItem with ID: {id}")
        feedback_item = storage.get_node(id, FeedbackItem)

        logging.info("Getting FeedbackItem's Source")
        source = storage.get_feedback_item_source(feedback_item)

        logging.info("Getting Text For Data Points")
        openai_interface = OpenAIInterface()
        data_points_text = openai_interface.get_data_points_text(source.text)
        data_points: List[DataPoint] = []

        for data_point_text in data_points_text:
            logging.info("Getting Embedding")
            embedding = openai_interface.get_embedding(data_point_text)

            logging.info("Creating Data Point")
            data_point = DataPoint(
                interpretation=data_point_text, embedding=str(embedding)
            )
            data_points.append(data_point)

            logging.info("Scoring Data Point")
            scores = openai_interface.score_data_point(
                data_point_text,
                source.text,
                [
                    ScoreType.SATISFACTION,
                    ScoreType.SPECIFICITY,
                    ScoreType.BUSINESS_IMPACT,
                ],
            )

            logging.info("Adding to Storage")
            storage.add_data_point_for_feedback_item(data_point, feedback_item)
            for score in scores:
                storage.add_score(data_point, score)

        logging.info("Updating the time at which data points were last modified")
        app_state = storage.get_app_state()
        app_state.data_points_last_modified = time.time()
        storage.update_app_state(app_state)

        logging.info("Getting new action items for feedback item")
        existing_action_items: List[ActionItem] = []  # Get from vectorsearch
        new_action_items = openai_interface.get_new_action_items(
            source.text, data_points, existing_action_items
        )
        for new_action_item in new_action_items:
            storage.add_action_item(new_action_item)

        logging.info("Adding edges between action items and data points")
        all_action_items = existing_action_items + new_action_items
        openai_interface.get_action_items_to_data_point_connections(
            source.text, data_points, all_action_items
        )

        return func.HttpResponse(f"Hanlded FeedbackItem Change.", status_code=200)

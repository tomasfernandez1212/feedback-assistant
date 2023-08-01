import logging
from typing import List
import time

import azure.functions as func

from src.data.dataPoint import DataPoint
from src.data.feedbackItems import FeedbackItem
from src.storage import Storage

from src.openai import OpenAIInterface


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Unpacking Request Body")
    req_body = req.get_json()
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting FeedbackItem with ID: {id}")
        feedback_item = storage.get_node(id, FeedbackItem)

        logging.info("Getting FeedbackItem's Source")
        source = storage.get_feedback_item_source(feedback_item)

        logging.info("Getting Data Point")
        openai_interface = OpenAIInterface()
        list_of_data_points = openai_interface.get_list_of_data_points(source.text)

        logging.info("Structuring Data Points")
        structured_data_points: List[DataPoint] = []
        for data_point in list_of_data_points:
            embedding = openai_interface.get_embedding(data_point)
            structured_data_points.append(
                DataPoint(interpretation=data_point, embedding=str(embedding))
            )

        logging.info("Adding Data Points to Graph")
        storage.add_data_points_for_feedback_item(structured_data_points, feedback_item)

        logging.info("Getting Strongly Consistancy Graph and Updating App State")
        app_state = storage.get_app_state()
        app_state.data_points_last_modified = time.time()
        storage.update_app_state(app_state)

        return func.HttpResponse(f"Hanlded FeedbackItem Change.", status_code=200)

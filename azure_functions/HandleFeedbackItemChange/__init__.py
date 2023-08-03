import logging
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

        logging.info("Getting Text For Data Points")
        openai_interface = OpenAIInterface()
        data_points_text = openai_interface.get_data_points_text(source.text)

        for data_point_text in data_points_text:
            logging.info("Getting Embedding")
            embedding = openai_interface.get_embedding(data_point_text)

            logging.info("Creating Data Point")
            data_point = DataPoint(
                interpretation=data_point_text, embedding=str(embedding)
            )

            logging.info("Scoring Data Point")
            scores = openai_interface.score_data_point_all_types(
                data_point_text, source.text
            )

            logging.info("Adding to Storage")
            storage.add_data_point_for_feedback_item(data_point, feedback_item)
            for score in scores:
                storage.add_score(data_point, score)

        logging.info("Getting Strongly Consistancy Graph and Updating App State")
        app_state = storage.get_app_state()
        app_state.data_points_last_modified = time.time()
        storage.update_app_state(app_state)

        return func.HttpResponse(f"Hanlded FeedbackItem Change.", status_code=200)

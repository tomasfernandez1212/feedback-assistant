import logging
from typing import List
import time

import azure.functions as func

from src.data.tags import Tag
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

        logging.info("Getting Tags")
        openai_interface = OpenAIInterface()
        list_of_tags = openai_interface.get_list_of_tags(source.text)

        logging.info("Structuring Tags")
        structured_tags: List[Tag] = []
        for tag in list_of_tags:
            embedding = openai_interface.get_embedding(tag)
            structured_tags.append(Tag(name=tag, embedding=str(embedding)))

        logging.info("Adding Tags to Graph")
        storage.add_tags_for_feedback_item(structured_tags, feedback_item)

        logging.info("Getting Strongly Consistancy Graph and Updating App State")
        app_state = storage.get_app_state()
        app_state.tags_last_modified = time.time()
        storage.update_app_state(app_state)

        return func.HttpResponse(f"Hanlded FeedbackItem Change.", status_code=200)

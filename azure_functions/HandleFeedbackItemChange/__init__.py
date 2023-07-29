import logging
from typing import List

import azure.functions as func

from src.graph.connect import GraphConnection
from src.graph.data.tags import Tag

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
    if len(result) != 1:
        raise Exception(
            f"FeedbackItem is not constituted by exactly one element. Count: {len(result)}"
        )
    review = result[0]

    logging.info("Getting Tags")
    openai_interface = OpenAIInterface()
    list_of_tags = openai_interface.get_list_of_tags(review.text)

    logging.info("Structuring Tags")
    structured_tags: List[Tag] = []
    for tag in list_of_tags:
        embedding = openai_interface.get_embedding(tag)
        structured_tags.append(Tag(name=tag, embedding=str(embedding)))

    logging.info("Adding Tags to Graph")
    graph.add_tags_for_feedback_item(structured_tags, feedback_item)

    return func.HttpResponse(f"Hanlded FeedbackItem Change.", status_code=200)

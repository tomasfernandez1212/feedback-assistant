import logging, json

import azure.functions as func
from src.storage import Storage
from src.data.observations import Observation
from src.data.topics import Topic
from src.data.actionItems import ActionItem
from src.llm.connections import (
    infer_observation_to_action_items_connections,
    infer_observation_to_topics_connections,
)

from src.llm.action_items import check_needs_action


def main(msg: func.ServiceBusMessage) -> None:
    logging.info("INIT: Unpacking Request Body")
    req_body = json.loads(msg.get_body())
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting Observation with ID: {id}")
        observation = storage.get_node(id, Observation)
        scores = storage.get_observation_scores(observation)

        if check_needs_action(scores):
            logging.info("Infer related Action Items")
            existing_action_items, scores = storage.search_semantically(  # type: ignore
                search_for=ActionItem,
                from_text=observation.text,
                top_k=10,
                min_score=0.0,
            )
            related_action_items = infer_observation_to_action_items_connections(
                observation, existing_action_items
            )
            storage.add_observation_to_action_items_edges(
                observation, related_action_items
            )
            logging.info(
                f"Observation: \n\n {observation.text} \n\nAddressed by Action Items: {related_action_items}\n\n"
            )

        logging.info("Infer related Topics")
        existing_topics, scores = storage.search_semantically(  # type: ignore
            search_for=Topic, from_text=observation.text, top_k=10, min_score=0.0
        )
        related_topics = infer_observation_to_topics_connections(
            observation, existing_topics
        )
        storage.add_observation_to_topics_edges(observation, related_topics)
        logging.info(
            f"Observation: \n\n {observation.text} \n\nBelongs to Topics: {related_topics}\n\n"
        )

    logging.info("DONE: Finished processing.")

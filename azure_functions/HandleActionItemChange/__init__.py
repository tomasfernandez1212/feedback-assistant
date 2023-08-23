import logging, json
from typing import List

import azure.functions as func
from src.storage import Storage
from src.data.observations import Observation
from src.data.actionItems import ActionItem
from src.data.topics import Topic
from src.llm.connections import (
    infer_action_item_to_observations_connections,
    infer_action_item_to_topics_connections,
)
from src.llm.action_items import check_needs_action


def main(msg: func.ServiceBusMessage) -> None:
    logging.info("Unpacking Request Body")
    req_body = json.loads(msg.get_body())
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting Action Item with ID: {id}")
        action_item = storage.get_node(id, ActionItem)

        logging.info("Infer related Observations")
        existing_observations, relevance = storage.search_semantically(  # type: ignore
            search_for=Observation, from_text=action_item.text, top_k=10, min_score=0.0
        )
        existing_observations_needing_action: List[Observation] = []
        for observation in existing_observations:
            scores = storage.get_observation_scores(observation)
            if check_needs_action(scores):
                existing_observations_needing_action.append(observation)
        related_observations = infer_action_item_to_observations_connections(
            action_item, existing_observations_needing_action
        )
        storage.add_action_item_to_observations_edges(action_item, related_observations)
        logging.info(
            f"Action Item: \n\n {action_item.text} \n\nAddresses Observations: {related_observations}\n\n"
        )

        logging.info("Infer related Topics")
        existing_topics, relevance = storage.search_semantically(  # type: ignore
            search_for=Topic, from_text=action_item.text, top_k=10, min_score=0.0
        )
        related_topics = infer_action_item_to_topics_connections(
            action_item, existing_topics
        )
        storage.add_action_item_to_topics_edges(action_item, related_topics)
        logging.info(
            f"Action Item: \n\n {action_item.text} \n\nAddresses Topics: {related_topics}\n\n"
        )

    logging.info("DONE: Finished processing.")

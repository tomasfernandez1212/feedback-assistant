import logging, json
from typing import List

import azure.functions as func

from src.data.feedbackItems import FeedbackItem
from src.data.actionItems import ActionItem
from src.data.topics import Topic
from src.storage import Storage

from src.llm.observations import generate_observations, Observation
from src.llm.action_items import generate_action_items, check_needs_action
from src.llm.topics import generate_topics
from src.llm.scores import score_observation, ScoreType


def main(msg: func.ServiceBusMessage) -> None:
    logging.info("INIT: Unpacking Request Body")
    req_body = json.loads(msg.get_body())
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"INIT: Getting FeedbackItem with ID: {id}")
        feedback_item = storage.get_node(id, FeedbackItem)

        logging.info("DATAPOINTS: Generating Observations")
        observations = generate_observations(feedback_item.text)
        observations_requiring_actions: List[Observation] = []
        for observation in observations:
            logging.info("DATAPOINTS: Scoring Observation")
            scores = score_observation(
                observation.text,
                feedback_item.text,
                [
                    ScoreType.SATISFACTION,
                    ScoreType.SPECIFICITY,
                    ScoreType.BUSINESS_IMPACT,
                ],
            )
            if check_needs_action(scores):
                observations_requiring_actions.append(observation)

            logging.info("DATAPOINTS: Adding to Storage")
            storage.add_observation_for_feedback_item(observation, feedback_item)
            for score in scores:
                storage.add_score(observation, score)

        logging.info("ACTIONITEMS: Generating new action items and adding to storage")
        existing_action_items, scores = storage.search_semantically(
            search_for=ActionItem, from_text=feedback_item.text, top_k=10, min_score=0.0
        )
        new_action_items = generate_action_items(
            feedback_item.text, observations_requiring_actions, existing_action_items
        )
        for new_action_item in new_action_items:
            storage.add_action_item(new_action_item)

        logging.info("TOPICS: Generating new topics and adding to storage")
        existing_topics, scores = storage.search_semantically(
            search_for=Topic, from_text=feedback_item.text, top_k=10, min_score=0.0
        )
        new_topics = generate_topics(feedback_item.text, observations, existing_topics)
        for new_topic in new_topics:
            storage.add_topic(new_topic)

    logging.info("DONE: Finished processing.")

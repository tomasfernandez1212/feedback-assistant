import logging, json

import azure.functions as func
from src.storage import Storage
from src.data.observations import Observation
from src.data.topics import Topic
from src.llm.connections import infer_topic_to_observations_connections


def main(msg: func.ServiceBusMessage) -> None:
    logging.info("INIT: Unpacking Request Body")
    req_body = json.loads(msg.get_body())
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting Topic with ID: {id}")
        topic = storage.get_node(id, Topic)

        logging.info("Infer related Observations")
        existing_observations, scores = storage.search_semantically(  # type: ignore
            search_for=Observation, from_text=topic.text, top_k=10, min_score=0.0
        )
        related_observations = infer_topic_to_observations_connections(
            topic, existing_observations
        )
        storage.add_topic_to_observations_edges(topic, related_observations)
        logging.info(
            f"Topic: \n\n {topic.text} \n\nContains Observations: {related_observations}\n\n"
        )

    logging.info("DONE: Finished processing.")

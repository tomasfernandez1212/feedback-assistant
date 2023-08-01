import logging
from typing import List

import azure.functions as func
from src.storage import Storage
from src.data.tags import Tag
from src.data.topics import Topic
from src.clustering import cluster_embeddings
from src.openai import OpenAIInterface
import time


def main(mytimer: func.TimerRequest) -> None:
    logging.info("Starting timer function.")
    current_time = time.time()

    if mytimer.past_due:
        logging.info("The timer was running late, but is the function is now running.")

    with Storage() as storage:
        logging.info("Getting Storage Connection and Checking App State")
        app_state = storage.get_app_state()
        if app_state.tags_clustering_last_started > app_state.tags_last_modified:
            logging.info("Tags Clustering Already Started. Ending.")
            return
        else:
            app_state.tags_clustering_last_started = current_time
            storage.update_app_state(app_state)

        logging.info("Loading Tags.")
        tags = storage.get_all_nodes_by_type(Tag)
        if len(tags) == 0:
            logging.info("No Tags Found. Ending.")
            return

        logging.info("Constructing Embeddings Matrix")
        embeddings: List[List[float]] = []
        for tag in tags:
            embeddings.append(eval(tag.embedding))

        logging.info("Clustering")
        cluster_ids = cluster_embeddings(embeddings)

        logging.info("Organize Tags by Cluster")
        cluster_to_tags: dict[int, List[Tag]] = {}
        for tag, cluster_id in zip(tags, cluster_ids):
            if cluster_id not in cluster_to_tags:
                cluster_to_tags[cluster_id] = []
            cluster_to_tags[cluster_id].append(tag)

        logging.info("Get Topic Name Per Cluster from Tags")
        openai_interface = OpenAIInterface()
        for cluster_id, tags in cluster_to_tags.items():
            topic_name = openai_interface.get_topic_from_tags(
                [tag.name for tag in tags]
            )
            logging.info(f"Topic Name: {topic_name}")
            topic = Topic(name=topic_name)
            storage.add_topic_based_on_tags(topic, tags)

        logging.info("Done")

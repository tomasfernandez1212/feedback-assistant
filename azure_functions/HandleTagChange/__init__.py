import logging
from typing import List

import azure.functions as func
from src.graph.connect import GraphConnection
from src.graph.data.tags import Tag
from src.graph.data.topics import Topic
from src.clustering import cluster_embeddings
from src.openai import OpenAIInterface
import time


def main(mytimer: func.TimerRequest) -> None:
    logging.info("Starting timer function.")
    current_time = time.time()

    if mytimer.past_due:
        logging.info("The timer was running late, but is the function is now running.")

    logging.info("Getting Strongly Consistancy Graph and Checking App State")
    graph_strong = GraphConnection(strong_consistency=True)
    app_state = graph_strong.get_app_state()
    if app_state.tags_clustering_last_started > app_state.tags_last_modified:
        logging.info("Tags Clustering Already Started. Ending.")
        graph_strong.close()
        return
    else:
        app_state.tags_clustering_last_started = current_time
        graph_strong.update_app_state(app_state)
        graph_strong.close()

    logging.info("Getting General Graph Connection")
    graph = GraphConnection()

    logging.info("Loading Tags.")
    tags = graph.get_all_nodes_by_type(Tag)
    if len(tags) == 0:
        logging.info("No Tags Found. Ending.")
        graph.close()
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
        topic_name = openai_interface.get_topic_from_tags([tag.name for tag in tags])
        logging.info(f"Topic Name: {topic_name}")
        topic = Topic(name=topic_name)
        graph.add_topic_based_on_tags(topic, tags)

    logging.info("Done")
    graph.close()

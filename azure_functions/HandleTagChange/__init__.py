import logging
from typing import List

import azure.functions as func
from src.graph.connect import GraphConnection
from src.graph.data.tags import Tag
from src.clustering import cluster_embeddings


def main(mytimer: func.TimerRequest) -> None:
    logging.info("Starting timer function.")

    if mytimer.past_due:
        logging.info("The timer was running late, but is the function is now running.")

    logging.info("Connect to Graph")

    logging.info("Loading Tags.")
    graph = GraphConnection()
    tags = graph.get_all_nodes_by_type(Tag)

    logging.info("Constructing Embeddings Matrix")
    embeddings: List[List[float]] = []
    for tag in tags:
        embeddings.append(eval(tag.embedding))

    logging.info("Clustering")
    cluster_ids = cluster_embeddings(embeddings)

    print(cluster_ids)

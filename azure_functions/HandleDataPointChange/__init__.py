import logging
from typing import List

import azure.functions as func
from src.storage import Storage
from src.data.dataPoint import DataPoint
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
        if (
            app_state.data_points_clustering_last_started
            > app_state.data_points_last_modified
        ):
            logging.info("Data Point Clustering Already Started. Ending.")
            return
        else:
            app_state.data_points_clustering_last_started = current_time
            storage.update_app_state(app_state)

        logging.info("Loading Data Points.")
        data_points = storage.get_all_nodes_by_type(DataPoint)
        if len(data_points) == 0:
            logging.info("No Data Points Found. Ending.")
            return

        logging.info("Constructing Embeddings Matrix")
        embeddings: List[List[float]] = []
        for data_point in data_points:
            embeddings.append(eval(data_point.embedding))

        logging.info("Clustering")
        cluster_ids = cluster_embeddings(embeddings)

        logging.info("Organize Data Points by Cluster")
        cluster_to_data_points: dict[int, List[DataPoint]] = {}
        for data_point, cluster_id in zip(data_points, cluster_ids):
            if cluster_id not in cluster_to_data_points:
                cluster_to_data_points[cluster_id] = []
            cluster_to_data_points[cluster_id].append(data_point)

        logging.info("Clearing Topics")
        storage.clear_topics()

        logging.info("Get Topic Name And Add to Storage")
        openai_interface = OpenAIInterface()
        for cluster_id, data_points in cluster_to_data_points.items():
            topic_name = openai_interface.get_topic_from_data_points(
                [data_point.interpretation for data_point in data_points]
            )
            topic = Topic(name=topic_name)
            storage.add_topic_based_on_data_points(topic, data_points)
            logging.info(f"Topic: {topic_name}")
            logging.info(
                f"Data Points: {[data_point.interpretation for data_point in data_points]}"
            )

        logging.info("Done")

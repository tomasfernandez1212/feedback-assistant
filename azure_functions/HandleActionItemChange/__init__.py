import logging, json

import azure.functions as func
from src.storage import Storage
from src.data.dataPoint import DataPoint
from src.data.actionItems import ActionItem
from src.llm.connections import infer_action_item_to_data_points_connections


def main(msg: func.ServiceBusMessage) -> None:
    logging.info("Unpacking Request Body")
    req_body = json.loads(msg.get_body())
    id: str = req_body.get("id")

    with Storage() as storage:
        logging.info(f"Getting Action Item with ID: {id}")
        action_item = storage.get_node(id, ActionItem)

        logging.info("Infer related Data Points")
        existing_data_points, scores = storage.search_semantically(  # type: ignore
            search_for=DataPoint, from_text=action_item.text, top_k=10, min_score=0.0
        )
        related_data_points = infer_action_item_to_data_points_connections(
            action_item, existing_data_points
        )
        storage.add_action_item_to_data_points_edges(action_item, related_data_points)
        logging.info(
            f"Action Item: \n\n {action_item.text} \n\nContains Data Points: {related_data_points}\n\n"
        )

    logging.info("DONE: Finished processing.")

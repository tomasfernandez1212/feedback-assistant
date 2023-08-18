import logging
from datetime import datetime
from azure.functions import DocumentList, Out

LABELS_WITH_QUEUES = ["FeedbackItem", "DataPoint", "ActionItem", "Topic"]


def send_to_queue(node_id: str, node_label: str, node_str: str, queue: Out[str]):
    info = f"send message to {node_label} queue for {node_id}"
    logging.info(f"Attempting: {info}")
    try:
        queue.set(node_str)  # type: ignore
        logging.info(f"Success: {info}")
    except Exception as e:
        logging.info(f"Failure: {info}")
        logging.info(e)


def main(
    documents: DocumentList,
    feedbackitemchangequeue: Out[str],
    datapointchangequeue: Out[str],
    actionitemchangequeue: Out[str],
    topicchangequeue: Out[str],
):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Python function started at {current_time}")

    # Loop through documents with changes
    for node in documents:  # type: ignore
        node_id: str = node["id"]  # type: ignore
        node_label: str = node["label"]  # type: ignore
        node_str: str = node.to_json()  # type: ignore

        logging.info(
            f"Detected change to {node_id} of type {node_label} at {current_time}"
        )

        # Send node to appropriate queue
        if node_label == "FeedbackItem":
            send_to_queue(node_id, node_label, node_str, feedbackitemchangequeue)  # type: ignore
        elif node_label == "DataPoint":
            send_to_queue(node_id, node_label, node_str, datapointchangequeue)  # type: ignore
        elif node_label == "ActionItem":
            send_to_queue(node_id, node_label, node_str, actionitemchangequeue)  # type: ignore
        elif node_label == "Topic":
            send_to_queue(node_id, node_label, node_str, topicchangequeue)  # type: ignore
        else:
            logging.info(
                f"Node {node_id} of type {node_label} does not have a queue to send to."
            )

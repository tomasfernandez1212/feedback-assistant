import logging
from datetime import datetime
from azure.functions import DocumentList, Out


def main(
    documents: DocumentList,
    feedbackitemchangequeue: Out[str],
    datapointchangequeue: Out[str],
):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Python function started at {current_time}")

    for node in documents:  # type: ignore
        node_id: str = node["id"]  # type: ignore
        node_label: str = node["label"]  # type: ignore
        node_str: str = node.to_json()  # type: ignore

        logging.info(
            f"Detected change to {node_id} of type {node_label} at {current_time}"
        )
        logging.info(f"Node: {node_str}")

        if node_label == "FeedbackItem":
            feedbackitemchangequeue.set(node_str)  # type: ignore
        elif node_label == "DataPoint":
            datapointchangequeue.set(node_str)  # type: ignore
        else:
            logging.info(
                f"Node {node_id} of type {node_label} does not have a queue to send to."
            )

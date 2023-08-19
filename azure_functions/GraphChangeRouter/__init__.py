import logging
from datetime import datetime
from azure.functions import DocumentList, Out

LABELS_WITH_QUEUES = ["FeedbackItem", "DataPoint", "ActionItem", "Topic"]


def main(
    documents: DocumentList,
    feedbackitemchangequeue: Out[str],
    datapointchangequeue: Out[str],
    actionitemchangequeue: Out[str],
    topicchangequeue: Out[str],
):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Python function started at {current_time}")

    if len(documents) > 1:
        logging.error(
            "More than one document was passed to the function. The output binding to the azure service bus queue can only send one message at a time. Set the maxItemsPerInvocation to 1 in the input binding."
        )
        return

    node = documents[0]  # type: ignore

    node_id: str = node["id"]  # type: ignore
    node_label: str = node["label"]  # type: ignore
    node_str: str = node.to_json()  # type: ignore

    logging.info(f"Detected change to {node_id} of type {node_label} at {current_time}")

    # Send node to appropriate queue
    if node_label == "FeedbackItem":
        feedbackitemchangequeue.set(node_str)  # type: ignore
    elif node_label == "DataPoint":
        datapointchangequeue.set(node_str)  # type: ignore
    elif node_label == "ActionItem":
        actionitemchangequeue.set(node_str)  # type: ignore
    elif node_label == "Topic":
        topicchangequeue.set(node_str)  # type: ignore
    else:
        logging.info(
            f"Node {node_id} of type {node_label} does not have a queue to send to."
        )

    logging.info(f"Python function finished.")

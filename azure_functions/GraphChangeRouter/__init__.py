import logging
from datetime import datetime

import os
from typing import Dict, List

from azure.servicebus.aio import ServiceBusClient, ServiceBusSender
from azure.servicebus import ServiceBusMessage

from azure.functions import DocumentList

NAMESPACE_CONNECTION_STR = os.environ["MESSAGE_QUEUE_CONNECTION"]
LABELS_WITH_QUEUE: List[str] = ["FeedbackItem", "DataPoint"]


def label_to_queue_name(label: str) -> str:
    return f"{label.lower()}changequeue"


ALL_QUEUE_NAMES = [label_to_queue_name(label) for label in LABELS_WITH_QUEUE]


def init_servicebus_senders() -> Dict[str, ServiceBusSender]:
    servicebus_client = ServiceBusClient.from_connection_string(
        conn_str=NAMESPACE_CONNECTION_STR, logging_enable=True
    )

    senders: Dict[str, ServiceBusSender] = {}
    for queue_name in ALL_QUEUE_NAMES:
        senders[queue_name] = servicebus_client.get_queue_sender(queue_name=queue_name)
    return senders


def main(
    documents: DocumentList,
):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Python function started at {current_time}")

    senders = init_servicebus_senders()

    for node in documents:  # type: ignore
        node_id: str = node["id"]  # type: ignore
        node_label: str = node["label"]  # type: ignore

        logging.info(
            f"Detected change to {node_id} of type {node_label} at {current_time}"
        )
        logging.info(f"Node: {node.to_json()}")  # type: ignore

        if node_label in LABELS_WITH_QUEUE:
            queue_name = label_to_queue_name(node_label)  # type: ignore
            sender = senders[queue_name]
            sender.send(ServiceBusMessage(node.to_json()))  # type: ignore
        else:
            logging.info(
                f"Node {node_id} of type {node_label} does not have a queue to send to."
            )

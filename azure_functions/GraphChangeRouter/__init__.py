import logging
from datetime import datetime
import os
import json
import threading
import requests

from azure.functions import DocumentList

FUNCTION_APP_NAME = "fa-function-app"


def call_function(function_name: str, body: dict[str, str]):
    # Get Function Key
    function_key = os.environ[f"{function_name}_KEY"]
    if function_key == "":
        raise Exception(f"{function_name}_KEY is not set")

    # Create URL
    logging.info(f"Calling {function_name}.")
    url = f"https://{FUNCTION_APP_NAME}.azurewebsites.net/api/{function_name}?code={function_key}"

    # This starts the request, but doesn't wait for the response
    threading.Thread(target=requests.post, args=(url,), kwargs={"json": body}).start()


def main(documents: DocumentList):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for node in documents:  # type: ignore
        id = node["id"]  # type: ignore
        label = node["label"]  # type: ignore

        logging.info(f"Detected change to {id} of type {label} at {current_time}")
        logging.info(f"Node: {node.to_json()}")  # type: ignore

        if label == "FeedbackItem":
            call_function("HandleFeedbackItemChange", json.loads(node.to_json()))  # type: ignore
        elif label == "DataPoint":
            call_function("HandleDataPointChange", json.loads(node.to_json()))  # type: ignore
        elif label == "Topic":
            call_function("HandleTopicChange", json.loads(node.to_json()))  # type: ignore
        elif label == "ActionItem":
            call_function("HandleActionItemChange", json.loads(node.to_json()))  # type: ignore
        else:
            logging.info(f"Unknown node type: {label}")

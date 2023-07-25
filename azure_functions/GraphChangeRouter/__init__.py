import logging
from datetime import datetime
import os
import json
import requests

from azure.functions import DocumentList

FUNCTION_FOR_LABEL = {
    "Review": "HandleReviewChange",
}

FUNCTION_APP_NAME = "feedback-assistant-function-app"


def call_function(function_name: str, body: dict[str, str]):
    function_key = os.environ[f"{function_name}_KEY"]
    if function_key == "":
        raise Exception(f"{function_name}_KEY is not set")
    logging.info(f"Calling {function_name} with body {body}")
    url = f"https://{FUNCTION_APP_NAME}.azurewebsites.net/api/{function_name}?code={function_key}"
    response = requests.post(url, json=body)
    return response


def main(nodes: DocumentList):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for node in nodes:  # type: ignore
        id = node["id"]  # type: ignore
        label = node["label"]  # type: ignore

        logging.info(f"Detected change to {id} of type {label} at {current_time}.")

        if label not in FUNCTION_FOR_LABEL:
            logging.info(f"Label {label} does not have a handling function.")
            continue

        handling_function_name = FUNCTION_FOR_LABEL[label]  # type: ignore
        call_function(handling_function_name, json.loads(node.to_json()))  # type: ignore

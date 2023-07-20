import logging
from datetime import datetime

import azure.functions as func

FUNCTION_FOR_LABEL = {
    "review": "handleReviewChange",
}


def main(documents: list[dict[str, str]]):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for document in documents:
        id = document["id"]
        label = document["label"]

        logging.info(f"Detected change to {id} of type {label} at {current_time}.")

        if label not in FUNCTION_FOR_LABEL:
            logging.info(f"Label {label} does not have a handling function.")
            continue

        handling_function_name = FUNCTION_FOR_LABEL[label]

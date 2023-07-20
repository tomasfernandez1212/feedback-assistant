import logging

import azure.functions as func

FUNCTION_FOR_LABEL = {
    "review": "handleReviewChange",
}


def main(documents: func.DocumentList) -> str:
    current_time = func.utcnow().replace(microsecond=0).isoformat()

    for document in documents:
        id = document["id"]
        label = document["label"]

        logging.info(f"Detected change to {id} of type {label} at {current_time}.")

        if label not in FUNCTION_FOR_LABEL:
            logging.info(f"Label {label} does not have a handling function.")
            continue

        handling_function_name = FUNCTION_FOR_LABEL[label]

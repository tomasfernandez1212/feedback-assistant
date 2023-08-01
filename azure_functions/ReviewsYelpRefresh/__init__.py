import datetime
import logging

import azure.functions as func

import os
from apify_client import ApifyClient
from src.apify import YelpReviewsInterface

from src.storage import Storage


def main(mytimer: func.TimerRequest) -> None:
    # Log Time
    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )
    logging.info("Python timer trigger function ran at %s", utc_timestamp)

    # Initialize the ApifyClient with your API token
    apify_client = ApifyClient(os.environ["APIFY_API_TOKEN"])

    # Scrape Yelp
    yelp_reviews_interface = YelpReviewsInterface(apify_client)
    structured_reviews = yelp_reviews_interface.get(
        yelp_direct_url="https://www.yelp.com/biz/souvla-san-francisco-3?osq=souvla",
        review_limit=2,
    )

    # Add Reviews to Graph
    with Storage() as storage:
        storage.add_nodes(structured_reviews)

    logging.info("Done")

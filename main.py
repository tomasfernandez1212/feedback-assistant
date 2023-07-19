import os
from apify_client import ApifyClient
from apify import YelpReviewsInterface

from graph.connect import GraphConnection

# Initialize the ApifyClient with your API token
apify_client = ApifyClient(os.environ["APIFY_API_TOKEN"])

# Scrape Yelp
yelp_reviews_interface = YelpReviewsInterface(apify_client)
structured_reviews = yelp_reviews_interface.get(
    yelp_direct_url="https://www.yelp.com/biz/souvla-san-francisco-3?osq=souvla",
    review_limit=2,
)

# Add reviews to graph if they don't already exist
graph = GraphConnection()
graph.add_reviews(structured_reviews)

print("Done")

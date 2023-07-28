from dotenv import load_dotenv

load_dotenv()

from apify_client import ApifyClient

from typing import List
from pydantic import BaseModel

from src.graph.data.misc import RATING_MAPPING
from src.graph.data.reviews import Review, ReviewSource


class ApifyYelpReview(BaseModel):
    date: str
    rating: int
    text: str
    id: str


class ApifyYelpLocation(BaseModel):
    directUrl: str
    reviews: List[ApifyYelpReview]


class YelpReviewsInterface:
    """
    Scrape Yelp reviews using Apify's Yelp Scraper actor
    """

    def __init__(self, apify_client: ApifyClient) -> None:
        # Init Inputs
        self.apify_client = apify_client

        # Init Outputs
        self.raw_reviews_for_locations: List[ApifyYelpLocation] = []
        self.structured_reviews: List[Review] = []

    def _prepare_for_call(self, yelp_direct_url: str, review_limit: int) -> None:
        self.yelp_direct_urls = [yelp_direct_url]
        self.apify_actor_input = {
            "directUrls": self.yelp_direct_urls,
            "maxImages": 0,
            "reviewLimit": review_limit,
            "scrapeReviewerName": False,
            "scrapeReviewerUrl": False,
            "reviewsLanguage": "ALL",
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
            "maxRequestRetries": 10,
        }

    def _call_scraper(self) -> None:
        actor_client = self.apify_client.actor("yin/yelp-scraper")
        actor_result = actor_client.call(run_input=self.apify_actor_input)  # type: ignore
        dataset_id = actor_result["defaultDatasetId"]  # type: ignore
        self.apify_dataset = self.apify_client.dataset(dataset_id)  # type: ignore
        items = self.apify_dataset.list_items().items  # type: ignore
        self.raw_reviews_for_locations = [ApifyYelpLocation.parse_obj(item) for item in items]  # type: ignore

    def _structure_results(self) -> None:
        raw_location = self.raw_reviews_for_locations[0]  # Supports 1

        for raw_review in raw_location.reviews:
            review = Review(
                date=raw_review.date,
                rating=RATING_MAPPING[raw_review.rating],
                text=raw_review.text,
                source=ReviewSource.YELP,
                source_review_id=raw_review.id,
            )

            self.structured_reviews.append(review)

    def get(self, yelp_direct_url: str, review_limit: int) -> List[Review]:
        """
        Run the scraper and return the structured results.

        The structured results are a dictionary with the direct url as the key and a list of structured reviews as the value.

        yelp_direct_url: The direct url to the Yelp business page you want to scrape.
        review_limit: The maximum number of reviews to scrape.
        """
        self._prepare_for_call(yelp_direct_url, review_limit)
        self._call_scraper()
        self._structure_results()
        return self.structured_reviews

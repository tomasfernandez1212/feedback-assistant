from dotenv import load_dotenv

load_dotenv()

from apify_client import ApifyClient
import os

from dataclasses import dataclass
from enum import Enum, auto
from typing import List
from pydantic import BaseModel


class Rating(Enum):
    ONE = auto()
    TWO = auto()
    THREE = auto()
    FOUR = auto()
    FIVE = auto()


rating_mapping = {
    1: Rating.ONE,
    2: Rating.TWO,
    3: Rating.THREE,
    4: Rating.FOUR,
    5: Rating.FIVE,
}


class Source(Enum):
    YELP = auto()
    OTHER = auto()


@dataclass
# rating with enum
class Review:
    date: str
    rating: Rating
    text: str
    source: Source
    source_review_id: str


class ApifyYelpReview(BaseModel):
    date: str
    rating: int
    text: str
    id: str


class ApifyYelpLocation(BaseModel):
    directUrl: str
    reviews: List[ApifyYelpReview]


class YelpReviews:
    """
    Scrape Yelp reviews using Apify's Yelp Scraper actor
    """

    def __init__(
        self,
        apify_client: ApifyClient,
        yelp_direct_url: str,
        review_limit: int = 9999,
    ) -> None:
        # Init Inputs
        self.apify_client = apify_client
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

        # Init Outputs
        self.raw_reviews_for_locations: list[ApifyYelpLocation] = []
        self.structured_results: dict[str, list[Review]] = {}

    def _call_scraper(self) -> None:
        actor_client = self.apify_client.actor("yin/yelp-scraper")
        actor_result = actor_client.call(run_input=self.apify_actor_input)  # type: ignore
        dataset_id = actor_result["defaultDatasetId"]  # type: ignore
        self.apify_dataset = self.apify_client.dataset(dataset_id)  # type: ignore
        items = self.apify_dataset.list_items().items  # type: ignore
        self.raw_reviews_for_locations = [ApifyYelpLocation.parse_obj(item) for item in items]  # type: ignore

    def _structure_results(self) -> None:
        for raw_location in self.raw_reviews_for_locations:
            reviews: list[Review] = []

            for raw_review in raw_location.reviews:
                review = Review(
                    date=raw_review.date,
                    rating=rating_mapping[raw_review.rating],
                    text=raw_review.text,
                    source=Source.YELP,
                    source_review_id=raw_review.id,
                )

                reviews.append(review)

            self.structured_results[raw_location.directUrl] = reviews

    def run(self) -> dict[str, list[Review]]:
        """
        Run the scraper and return the structured results.

        The structured results are a dictionary with the direct url as the key and a list of structured reviews as the value.
        """
        self._call_scraper()
        self._structure_results()
        return self.structured_results


class GraphInterface:
    def add_review(self, review: Review) -> None:
        pass


# Initialize the ApifyClient with your API token
apify_client = ApifyClient(os.environ["APIFY_API_TOKEN"])

# Scrape Yelp
yelp_reviews = YelpReviews(
    apify_client,
    yelp_direct_url="https://www.yelp.com/biz/souvla-san-francisco-3?osq=souvla",
    review_limit=2,
)
structured_reviews = yelp_reviews.run()

print(structured_reviews)

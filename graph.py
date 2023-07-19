from enum import Enum, auto
from dataclasses import dataclass


class Rating(Enum):
    ONE = auto()
    TWO = auto()
    THREE = auto()
    FOUR = auto()
    FIVE = auto()


RATING_MAPPING = {
    1: Rating.ONE,
    2: Rating.TWO,
    3: Rating.THREE,
    4: Rating.FOUR,
    5: Rating.FIVE,
}


class ReviewSource(Enum):
    YELP = auto()
    OTHER = auto()


@dataclass
class Review:
    date: str
    rating: Rating
    text: str
    source: ReviewSource
    source_review_id: str


class GraphConnection:
    def add_review(self, review: Review) -> None:
        pass

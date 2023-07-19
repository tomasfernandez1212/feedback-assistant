from dataclasses import dataclass
from enum import Enum, auto

from graph.data.misc import Rating


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

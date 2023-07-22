from dataclasses import dataclass
from enum import Enum, auto
from pydantic import BaseModel

from src.graph.data.misc import Rating


class ReviewSource(Enum):
    YELP = auto()
    OTHER = auto()


@dataclass
class Review(BaseModel):
    date: str
    rating: Rating
    text: str
    source: ReviewSource
    source_review_id: str

    def __post_init__(self):
        self.review_id = self.source.name + self.source_review_id

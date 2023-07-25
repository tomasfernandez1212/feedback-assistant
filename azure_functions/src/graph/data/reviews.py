from enum import Enum, auto
from typing import Any
from pydantic import BaseModel

from src.graph.data.misc import Rating


class ReviewSource(Enum):
    YELP = auto()
    OTHER = auto()


class Review(BaseModel):
    date: str
    rating: Rating
    text: str
    source: ReviewSource
    source_review_id: str
    review_id: str = ""

    def model_post_init(self, __context: Any) -> None:
        self.review_id = self.source.name + self.source_review_id

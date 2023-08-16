from enum import Enum, auto
from pydantic import BaseModel
from typing import Any
import time

from src.data.misc import Rating


class ReviewSource(Enum):
    YELP = auto()
    OTHER = auto()


class Review(BaseModel):
    rating: Rating
    source: ReviewSource
    source_review_id: str
    id: str = ""
    created_at: float = 0

    def model_post_init(self, __context: Any) -> None:
        self.id: str = f"{self.__class__.__name__}_{self.source.name}_{self.source_review_id}"  # Add ID
        if self.created_at == 0:
            self.created_at = time.time()
        return super().model_post_init(__context)

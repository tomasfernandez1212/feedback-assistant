from enum import Enum, auto
from pydantic import BaseModel
from typing import Any

from src.data.misc import Rating


class ReviewSource(Enum):
    YELP = auto()
    OTHER = auto()


class Review(BaseModel):
    date: str
    rating: Rating
    text: str
    source: ReviewSource
    source_review_id: str
    id: str = ""

    def model_post_init(self, __context: Any) -> None:
        self.id: str = f"{self.source.name}_{self.source_review_id}"  # Add ID
        self.text: str = self._clean_text(self.text)  # Clean Text
        return super().model_post_init(__context)

    def _clean_text(self, text: str) -> str:
        text = text.replace("\n", "\\n").replace("'", "\\'")
        return text

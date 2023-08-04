from typing import Any
from pydantic import BaseModel
from uuid import uuid4


class FeedbackItem(BaseModel):
    timestamp: int
    id: str = ""

    def model_post_init(self, __context: Any) -> None:
        if self.id == "":
            self.id: str = f"{self.__class__.__name__}_{str(uuid4())}"
        return super().model_post_init(__context)

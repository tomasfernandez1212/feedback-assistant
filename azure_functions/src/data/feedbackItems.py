from typing import Any
from pydantic import BaseModel
from uuid import uuid4
import time


class FeedbackItem(BaseModel):
    text: str
    text_written_at: float
    node_created_at: float = 0
    id: str = ""

    def model_post_init(self, __context: Any) -> None:
        if self.id == "":
            self.id: str = f"{self.__class__.__name__}_{str(uuid4())}"
        if self.node_created_at == 0:
            self.node_created_at = time.time()
        return super().model_post_init(__context)

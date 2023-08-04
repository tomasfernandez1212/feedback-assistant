from pydantic import BaseModel
from uuid import uuid4
from typing import Any
import time


class DataPoint(BaseModel):
    interpretation: str
    embedding: str  # Str for easier storage in Graph. Property can't be list of floats.
    id: str = ""
    created_at: float = 0

    def model_post_init(self, __context: Any) -> None:
        if self.id == "":
            self.id: str = f"{self.__class__.__name__}_{str(uuid4())}"
        if self.created_at == 0:
            self.created_at = time.time()
        return super().model_post_init(__context)

from pydantic import BaseModel
from uuid import uuid4
from typing import Any


class DataPoint(BaseModel):
    interpretation: str
    embedding: str  # Str for easier storage in Graph. Property can't be list of floats.
    id: str = ""

    def model_post_init(self, __context: Any) -> None:
        if self.id == "":
            self.id: str = str(uuid4())
        return super().model_post_init(__context)

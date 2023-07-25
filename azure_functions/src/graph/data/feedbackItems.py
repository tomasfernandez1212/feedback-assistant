from typing import Any
from pydantic import BaseModel, validator
from uuid import uuid4


class FeedbackItem(BaseModel):
    satisfaction_score: float
    timestamp: int
    id: str = ""

    def model_post_init(self, __context: Any) -> None:
        self.id: str = str(uuid4())
        return super().model_post_init(__context)

    @validator("satisfaction_score")
    def satisfaction_score_must_be_between_0_and_1(cls, satisfaction_score: float):
        if satisfaction_score < 0 or satisfaction_score > 1:
            raise ValueError("satisfaction_score must be between 0 and 1")
        return satisfaction_score

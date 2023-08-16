from pydantic import BaseModel


class AppState(BaseModel):
    id: str = "only_app_state"

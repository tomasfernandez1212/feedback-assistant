from pydantic import BaseModel


class AppState(BaseModel):
    tags_clustering_last_started: float = 0.0
    tags_last_modified: float = 0.0
    id: str = "only_app_state"

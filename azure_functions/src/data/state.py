from pydantic import BaseModel


class AppState(BaseModel):
    data_points_clustering_last_started: float = 0.0
    data_points_last_modified: float = 0.0
    id: str = "only_app_state"

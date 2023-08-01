import pytest


@pytest.fixture(scope="session", autouse=True)
def setup():
    import os

    os.environ["EVENTUAL_GRAPH_DB_NAME"] = (
        os.environ["EVENTUAL_GRAPH_DB_NAME"] + "-test"
    )
    os.environ["EVENTUAL_GRAPH_GRAPH_NAME"] = (
        os.environ["EVENTUAL_GRAPH_GRAPH_NAME"] + "-test"
    )

    os.environ["STRONG_GRAPH_DB_NAME"] = os.environ["STRONG_GRAPH_DB_NAME"] + "-test"
    os.environ["STRONG_GRAPH_GRAPH_NAME"] = (
        os.environ["STRONG_GRAPH_GRAPH_NAME"] + "-test"
    )

    from src.storage import Storage, Environment

    # Reset the eventual consistency test graph
    with Storage() as storage:
        storage.reset_storage(environment=Environment.TEST)

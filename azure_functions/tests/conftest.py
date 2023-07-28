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

    from src.graph.connect import GraphConnection

    # Reset the eventual consistency test graph
    graph = GraphConnection()
    graph.reset_graph("feedback-assistant-test")
    graph.close()

    # Reset the strong consistency test graph
    graph_strong = GraphConnection(strong_consistency=True)
    graph_strong.reset_graph("feedback-assistant-strong-consistency-test")
    graph_strong.close()

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup():
    import os

    os.environ["AZURE_COSMOS_DB_NAME"] = "sample-graph-test"
    os.environ["AZURE_COSMOS_GRAPH_NAME"] = "sample-graph-test"

    from src.graph.connect import GraphConnection

    graph = GraphConnection()
    graph.reset_graph("sample-graph-test")
    graph.close()

import pytest


@pytest.fixture(autouse=True)
def setup():
    import os

    os.environ["AZURE_COSMOS_DB_NAME"] = "sample-graph-test"
    os.environ["AZURE_COSMOS_GRAPH_NAME"] = "sample-graph-test"

    from src.graph.connect import GraphConnection
    from src.graph.data.reviews import Review, Rating, ReviewSource

    graph = GraphConnection()
    graph.reset_graph("sample-graph-test")
    graph.add_node(
        Review(
            text="I love this place! The food is amazing and the service is great!",
            rating=Rating.FIVE,
            date="2021-01-01T00:00:00Z",
            source=ReviewSource.YELP,
            source_review_id="9hHyzoRRlXr2tQFDXGSbmg",
        )
    )

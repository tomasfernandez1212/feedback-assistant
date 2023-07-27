from typing import Callable, Any
from ReviewsYelpRefresh import main
import azure.functions as func
from unittest.mock import patch, MagicMock
from unittest import mock
from src.graph.data.reviews import Review


class TestReviewsYelpRefresh:
    def setup_method(self, method: Callable[[], Any]):
        pass

    def teardown_method(self, method: Callable[[], Any]):
        pass

    # @pytest.mark.skip(reason="Expensive. Only run periodically.")
    def test_reviews_yelp_refresh(self):
        with patch(
            "src.apify.YelpReviewsInterface", new=MagicMock
        ) as mock_yelp_reviews_interface:
            with patch(
                "src.graph.connect.GraphConnection", new=MagicMock
            ) as mock_graph_connection:
                req = mock.Mock(spec=func.TimerRequest)
                main(req)

                assert (
                    len(mock_yelp_reviews_interface.return_value.structured_reviews) > 0
                )
                assert isinstance(
                    mock_yelp_reviews_interface.return_value.structured_reviews[0],
                    Review,
                )

                mock_graph_connection.return_value.add_nodes.assert_called_once_with(
                    mock.ANY
                )
                mock_graph_connection.return_value.close.assert_called_once_with()

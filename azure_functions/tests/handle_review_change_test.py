import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleReviewChange import main
from src.storage import Storage
from src.data.reviews import Review, Rating, ReviewSource


class TestHandleReviewChange(unittest.TestCase):
    def setup_method(self, method: Callable[[], Any]):
        with Storage() as storage:
            storage.add_node(
                Review(
                    text="I love this place! The food is amazing and the service is great!",
                    rating=Rating.FIVE,
                    date="2021-01-01T00:00:00Z",
                    source=ReviewSource.YELP,
                    source_review_id="9hHyzoRRlXr2tQFDXGSbmg",
                )
            )

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_review_change(self):
        req = mock.Mock(spec=func.HttpRequest)
        req.get_json.return_value = {"id": "Review_YELP_9hHyzoRRlXr2tQFDXGSbmg"}  # type: ignore

        resp = main(req)
        assert resp.status_code == 200

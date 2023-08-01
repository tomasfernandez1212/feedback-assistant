import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleFeedbackItemChange import main

from src.storage import Storage
from src.data.reviews import Review, Rating, ReviewSource
from src.data.feedbackItems import FeedbackItem


class TestFeedbackItemChange(unittest.TestCase):
    def setup_method(self, method: Callable[[], Any]):
        with Storage() as storage:
            # Add FeedbackItem with Edge
            review = Review(
                text="I didn't like this place! The food is bad and the service is terrible!",
                rating=Rating.ONE,
                date="2020-01-01T00:00:00Z",
                source=ReviewSource.YELP,
                source_review_id="7hHyzoRRlXr2tQFDXGSbmg",
            )
            storage.add_node(review)
            feedback_item = FeedbackItem(
                satisfaction_score=5, timestamp=123, id="feedback_item_id"
            )
            storage.add_feedback_item(feedback_item, constituted_by=review)

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_feedback_item_change(self):
        req = mock.Mock(spec=func.HttpRequest)
        req.get_json.return_value = {"id": "feedback_item_id"}  # type: ignore

        resp = main(req)

        assert resp.status_code == 200

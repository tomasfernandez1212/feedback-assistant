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
                rating=Rating.FOUR,
                date="2020-01-01T00:00:00Z",
                source=ReviewSource.YELP,
                source_review_id="7hHyzoRRlXr2tQFDXGSbmg",
            )
            storage.add_node(review)
            feedback_item = FeedbackItem(
                id="feedback_item_id",
                text="It looks a bit hole-in-the-wall but has a lovely back patio with heaters. You order at the front and they give you a number, so it's a fast-casual vibe.",
            )
            storage.add_feedback_item(feedback_item, constituted_by=review)

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_feedback_item_change(self):
        req = mock.Mock(spec=func.HttpRequest)
        req.get_json.return_value = {"id": "feedback_item_id"}  # type: ignore

        resp = main(req)

        assert resp.status_code == 200

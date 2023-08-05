import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleFeedbackItemChange import main

from src.storage import Storage
from src.data.reviews import Review, Rating, ReviewSource
from src.data.feedbackItems import FeedbackItem
from src.misc import iso_to_unix_timestamp


class TestFeedbackItemChange(unittest.TestCase):
    def setup_method(self, method: Callable[[], Any]):
        with Storage() as storage:
            # Add FeedbackItem with Edge
            review = Review(
                rating=Rating.FOUR,
                source=ReviewSource.YELP,
                source_review_id="7hHyzoRRlXr2tQFDXGSbmg",
            )
            feedback_item = FeedbackItem(
                id="feedback_item_id",
                text="It looks a bit hole-in-the-wall but has a lovely back patio with heaters. You order at the front and they give you a number, so it's a fast-casual vibe.",
                text_written_at=iso_to_unix_timestamp("2023-07-25T00:00:00.000Z"),
            )
            storage.add_feedback_item_and_source(feedback_item, source=review)

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_feedback_item_change(self):
        req = mock.Mock(spec=func.HttpRequest)
        req.get_json.return_value = {"id": "feedback_item_id"}  # type: ignore

        resp = main(req)

        assert resp.status_code == 200

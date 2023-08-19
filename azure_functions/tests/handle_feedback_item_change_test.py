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
            # feedback_item = FeedbackItem(
            #     id="feedback_item_id",
            #     text="Tried their their Sour Cherry Greek frozen yogurt and it was quite nice. Also tried their frozen yogurt that had baklava. Got takeout and the frozen yogurt was immediately delivered, so nothing too much to mention of their service. Although I will note they were friendly and helpful. Ambiance seems loud-ish but chill. Will definitely come here to try their food next time.",
            #     text_written_at=iso_to_unix_timestamp("2023-07-25T00:00:00.000Z"),
            # )
            storage.add_feedback_item_and_source(feedback_item, source=review)

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_feedback_item_change(self):
        req = mock.Mock(spec=func.ServiceBusMessage)
        req.get_body.return_value = '{"id": "feedback_item_id"}'  # type: ignore

        main(req)

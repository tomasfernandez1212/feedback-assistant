import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleDataPointChange import main
from src.storage import Storage
from src.data.dataPoint import DataPoint
from src.data.feedbackItems import FeedbackItem
from src.data.reviews import Review, Rating, ReviewSource
from src.misc import iso_to_unix_timestamp


class TestHandleDataPointChange(unittest.TestCase):
    def setup_method(self, method: Callable[[], Any]):
        with Storage() as storage:
            review = Review(
                rating=Rating.FOUR,
                source=ReviewSource.YELP,
                source_review_id="Review_485u0",
            )
            feedback_item = FeedbackItem(
                text="This place had a great atmosphere and the pastries were delicious!",
                text_written_at=iso_to_unix_timestamp("2023-07-25T00:00:00.000Z"),
            )
            storage.add_feedback_item_and_source(feedback_item, review)
            data_point_1 = DataPoint(
                interpretation="Great Atmosphere",
                id="DataPoint_4048u",
            )
            data_point_2 = DataPoint(
                interpretation="Pastries",
                id="DataPoint_fh5894",
            )
            storage.add_data_point_for_feedback_item(data_point_1, feedback_item)
            storage.add_data_point_for_feedback_item(data_point_2, feedback_item)

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_data_point_change(self):
        req = mock.Mock(spec=func.TimerRequest)
        req.past_due.return_value = False  # type: ignore

        main(req)

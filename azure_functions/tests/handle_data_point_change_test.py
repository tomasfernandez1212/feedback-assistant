import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleDataPointChange import main
from src.storage import Storage
from src.data.dataPoint import DataPoint
from src.data.feedbackItems import FeedbackItem
from src.data.actionItems import ActionItem
from src.data.topics import Topic
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
                text="I just love how simple Souvla's menu is and you really can't go wrong with anything. My favorite dish is the chicken salad, it tastes so fresh but I wish it were bigger.",
                text_written_at=iso_to_unix_timestamp("2023-07-25T00:00:00.000Z"),
            )
            data_point_1 = DataPoint(
                interpretation="The menu at Souvla is simple and all the dishes are highly recommended.",
                id="DataPoint_4048u",
            )
            data_point_2 = DataPoint(
                interpretation="The customer finds the chicken salad fresh and satisfying.",
                id="DataPoint_fh5894",
            )
            topic_1 = Topic(
                name="Chicken Salad",
            )
            action_item_1 = ActionItem(
                text="Consider making the size of the chicken salad bigger.",
            )
            storage.add_feedback_item_and_source(feedback_item, review)
            storage.add_data_point_for_feedback_item(data_point_1, feedback_item)
            storage.add_data_point_for_feedback_item(data_point_2, feedback_item)
            storage.add_topic(topic_1)
            storage.add_action_item(action_item_1)

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_data_point_change(self):
        req = mock.Mock(spec=func.HttpRequest)
        req.get_json.return_value = {"id": "DataPoint_4048u"}  # type: ignore

        resp = main(req)

        assert resp.status_code == 200

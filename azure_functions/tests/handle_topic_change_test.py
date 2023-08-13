import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleTopicChange import main
from src.storage import Storage
from src.data.dataPoint import DataPoint
from src.data.feedbackItems import FeedbackItem
from src.data.actionItems import ActionItem
from src.data.topics import Topic
from src.data.reviews import Review, Rating, ReviewSource
from src.misc import iso_to_unix_timestamp


class TestHandleTopicChange(unittest.TestCase):
    def setup_method(self, method: Callable[[], Any]):
        with Storage() as storage:
            review = Review(
                rating=Rating.FOUR,
                source=ReviewSource.YELP,
                source_review_id="fq3ff",
            )
            feedback_item = FeedbackItem(
                text="I loved the apple tart. However, my table was not clean.",
                text_written_at=iso_to_unix_timestamp("2023-07-25T00:00:00.000Z"),
            )
            data_point_1 = DataPoint(
                text="The customer loved the apple tart.",
                id="DataPoint_fhtgtg5894",
            )
            data_point_2 = DataPoint(
                text="The customer found the table dirty.",
                id="DataPoint_fgw4g",
            )
            topic = Topic(
                text="Cleanliness",
                id="Topic_fhtgtg5894",
            )
            action_item = ActionItem(
                text="Clean the tables.",
            )
            storage.add_feedback_item_and_source(feedback_item, review)
            storage.add_data_point_for_feedback_item(data_point_1, feedback_item)
            storage.add_data_point_for_feedback_item(data_point_2, feedback_item)
            storage.add_topic(topic)
            storage.add_action_item(action_item)
            storage.connect_nodes([action_item], [data_point_2])

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_topic_change(self):
        req = mock.Mock(spec=func.HttpRequest)
        req.get_json.return_value = {"id": "Topic_fhtgtg5894"}  # type: ignore
        resp = main(req)

        assert resp.status_code == 200

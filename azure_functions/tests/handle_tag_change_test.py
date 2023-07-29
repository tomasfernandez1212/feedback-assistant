import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleTagChange import main
from src.graph.connect import GraphConnection
from src.graph.data.tags import Tag
from src.graph.data.feedbackItems import FeedbackItem
from src.graph.data.reviews import Review, Rating, ReviewSource
import random


class TestHandleTagChange(unittest.TestCase):
    def setup_method(self, method: Callable[[], Any]):
        graph = GraphConnection()
        review = Review(
            text="This place had a great atmosphere and the pastries were delicious!",
            rating=Rating.FOUR,
            date="2020-01-01T00:00:00Z",
            source=ReviewSource.YELP,
            source_review_id="REVIEW_485u0",
        )
        feedback_item = FeedbackItem(satisfaction_score=85, timestamp=345)
        graph.add_feedback_item(feedback_item, review)
        tag_1 = Tag(
            name="Great Atmosphere",
            embedding=f"{[random.random() for _ in range(1536)]}",
            id="TAG_4048u",
        )
        tag_2 = Tag(
            name="Pastries",
            embedding=f"{[random.random() for _ in range(1536)]}",
            id="TAG_fh5894",
        )
        graph.add_tags_for_feedback_item([tag_1, tag_2], feedback_item)
        graph.close()

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_tag_change(self):
        req = mock.Mock(spec=func.TimerRequest)
        req.past_due.return_value = False  # type: ignore

        main(req)

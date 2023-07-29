import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleTagChange import main
from src.graph.connect import GraphConnection
from src.graph.data.tags import Tag
from src.graph.data.feedbackItems import FeedbackItem
import random


class TestHandleTagChange(unittest.TestCase):
    def setup_method(self, method: Callable[[], Any]):
        graph = GraphConnection()
        feedback_item = FeedbackItem(satisfaction_score=60, timestamp=345)
        graph.add_node(feedback_item)
        tag_1 = Tag(
            name="Great Atmosphere",
            embedding=f"{[random.random() for _ in range(1536)]}",
            id="TAG_1",
        )
        tag_2 = Tag(
            name="Pastries",
            embedding=f"{[random.random() for _ in range(1536)]}",
            id="TAG_2",
        )
        graph.add_nodes([tag_1, tag_2])
        graph.close()

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_tag_change(self):
        req = mock.Mock(spec=func.TimerRequest)
        req.past_due.return_value = False  # type: ignore

        main(req)

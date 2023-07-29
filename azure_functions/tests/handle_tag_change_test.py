import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleTagChange import main
from src.graph.connect import GraphConnection
from src.graph.data.tags import Tag


class TestHandleTagChange(unittest.TestCase):
    def setup_method(self, method: Callable[[], Any]):
        graph = GraphConnection()
        graph.add_nodes(
            [
                Tag(
                    name="Great Atmosphere",
                    embedding="[0.1, 0.2, 0.3]",
                    id="TAG_1",
                ),
                Tag(
                    name="Pastries",
                    embedding="[0.3, 0.2, 0.1]",
                    id="TAG_2",
                ),
            ]
        )
        graph.close()

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_review_change(self):
        req = mock.Mock(spec=func.TimerRequest)
        req.past_due.return_value = False  # type: ignore

        main(req)

import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleActionItemChange import main
from src.storage import Storage
from src.data.observations import Observation
from src.data.feedbackItems import FeedbackItem
from src.data.actionItems import ActionItem
from src.data.topics import Topic
from src.data.reviews import Review, Rating, ReviewSource
from src.misc import iso_to_unix_timestamp


class TestHandleActionItemChange(unittest.TestCase):
    def setup_method(self, method: Callable[[], Any]):
        with Storage() as storage:
            review = Review(
                rating=Rating.FOUR,
                source=ReviewSource.YELP,
                source_review_id="refwr",
            )
            feedback_item = FeedbackItem(
                text="I loved the ambiance, but the waitress could have been more attentive.",
                text_written_at=iso_to_unix_timestamp("2023-07-25T00:00:00.000Z"),
            )
            observation_1 = Observation(
                text="The customer loved the ambiance.",
                id="Observation_efr894",
            )
            observation_2 = Observation(
                text="The customer found the waitress inattentive.",
                id="Observation_ergvg",
            )
            topic = Topic(
                text="Service",
                id="Topic_ewaed",
            )
            action_item = ActionItem(
                text="Train waiters to be more attentive.",
                id="ActionItem_rfhwei",
            )
            storage.add_feedback_item_and_source(feedback_item, review)
            storage.add_observation_for_feedback_item(observation_1, feedback_item)
            storage.add_observation_for_feedback_item(observation_2, feedback_item)
            storage.add_topic(topic)
            storage.connect_nodes([topic], [observation_2])
            storage.add_action_item(action_item)

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_action_item_change(self):
        req = mock.Mock(spec=func.ServiceBusMessage)
        req.get_body.return_value = '{"id": "ActionItem_rfhwei"}'  # type: ignore
        main(req)

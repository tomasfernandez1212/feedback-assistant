import unittest
import azure.functions as func
from typing import Callable, Any
from unittest import mock

from HandleObservationChange import main
from src.storage import Storage
from src.data.observations import Observation
from src.data.feedbackItems import FeedbackItem
from src.data.actionItems import ActionItem
from src.data.topics import Topic
from src.data.reviews import Review, Rating, ReviewSource
from src.misc import iso_to_unix_timestamp


class TestHandleObservationChange(unittest.TestCase):
    def setup_method(self, method: Callable[[], Any]):
        with Storage() as storage:
            review = Review(
                rating=Rating.FOUR,
                source=ReviewSource.YELP,
                source_review_id="Review_rfref",
            )
            feedback_item = FeedbackItem(
                text="My favorite dish is the chicken salad, it tastes so fresh but I wish it were bigger.",
                text_written_at=iso_to_unix_timestamp("2023-07-25T00:00:00.000Z"),
            )
            observation_1 = Observation(
                text="The customer was dissappointed by the size of the chicken salad although they found it fresh and satisfying.",
                id="Observation_fh5894",
            )
            related_topic = Topic(
                text="Chicken Salad",
            )
            related_action_item = ActionItem(
                text="Consider making the size of the chicken salad bigger.",
            )
            storage.add_feedback_item_and_source(feedback_item, review)
            storage.add_observation_for_feedback_item(observation_1, feedback_item)
            storage.add_topic(related_topic)
            storage.add_action_item(related_action_item)

    def teardown_method(self, method: Callable[[], Any]):
        pass

    def test_handle_related_observation_change(self):
        req = mock.Mock(spec=func.ServiceBusMessage)
        req.get_body.return_value = '{"id": "Observation_fh5894"}'  # type: ignore
        main(req)

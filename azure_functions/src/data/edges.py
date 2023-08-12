from src.data import GraphNode
from src.data.reviews import Review
from src.data.feedbackItems import FeedbackItem
from src.data.dataPoint import DataPoint
from src.data.topics import Topic
from src.data.scores import Score
from src.data.actionItems import ActionItem

from typing import Tuple, Type, Dict

# Define a type for the tuple of from and to node types
NodePair = Tuple[Type[GraphNode], Type[GraphNode]]


def determine_edge_label(from_type: Type[GraphNode], to_type: Type[GraphNode]) -> str:
    # This dictionary contains the allowed mappings
    edge_mappings: Dict[NodePair, str] = {
        (Review, FeedbackItem): "constitutes",
        (FeedbackItem, Review): "constituted_by",
        (FeedbackItem, DataPoint): "derived",
        (DataPoint, FeedbackItem): "derived_from",
        (Score, DataPoint): "scores_for",
        (DataPoint, Score): "scored_by",
        (ActionItem, FeedbackItem): "addresses",
        (FeedbackItem, ActionItem): "addressed_by",
        (ActionItem, Topic): "addresses",
        (Topic, ActionItem): "addressed_by",
        (ActionItem, DataPoint): "addresses",
        (DataPoint, ActionItem): "addressed_by",
        (Topic, DataPoint): "contains",
        (DataPoint, Topic): "belongs_to",
        (Topic, FeedbackItem): "informed_by",
        (FeedbackItem, Topic): "informs",
    }

    # Check if the combination exists
    if (from_type, to_type) in edge_mappings:
        return edge_mappings[(from_type, to_type)]
    else:
        raise ValueError(f"Edge label for {from_type} -> {to_type} doesn't exist!")

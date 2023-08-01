from typing import Union, Sequence, TypeVar
from src.data.reviews import Review
from src.data.feedbackItems import FeedbackItem
from src.data.dataPoint import DataPoint
from src.data.topics import Topic
from src.data.state import AppState

# Create a Type for Any Graph Node
NodeType = Union[Review, FeedbackItem, DataPoint, Topic, AppState]

# Create a Type for a List of Graph Nodes
ListNodesType = Sequence[NodeType]

# Create a dictionary - used for mapping labels to classes
LABEL_TO_CLASS = {
    "Review": Review,
    "FeedbackItem": FeedbackItem,
    "DataPoint": DataPoint,
    "Topic": Topic,
    "AppState": AppState,
}

NodeTypeVar = TypeVar("NodeTypeVar", bound=NodeType)

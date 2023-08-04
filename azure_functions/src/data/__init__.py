from typing import Union, Sequence, TypeVar
from src.data.reviews import Review
from src.data.feedbackItems import FeedbackItem
from src.data.dataPoint import DataPoint
from src.data.topics import Topic
from src.data.state import AppState
from src.data.scores import Score
from src.data.actionItems import ActionItem


# Create a Type for Any Graph Node
NodeType = Union[Review, FeedbackItem, DataPoint, ActionItem, Score, Topic, AppState]

# Create a Type for a List of Graph Nodes
ListNodesType = Sequence[NodeType]

# Create a dictionary - used for mapping labels to classes
LABEL_TO_CLASS = {
    "Review": Review,
    "FeedbackItem": FeedbackItem,
    "DataPoint": DataPoint,
    "Score": Score,
    "Topic": Topic,
    "AppState": AppState,
    "ActionItem": ActionItem,
}

NodeTypeVar = TypeVar("NodeTypeVar", bound=NodeType)

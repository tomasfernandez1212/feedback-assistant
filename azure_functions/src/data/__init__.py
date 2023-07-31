from typing import Union, Sequence
from src.data.reviews import Review
from src.data.feedbackItems import FeedbackItem
from src.data.tags import Tag
from src.data.topics import Topic
from src.data.state import AppState

# Create a Type for Any Graph Node
NodeType = Union[Review, FeedbackItem, Tag, Topic, AppState]

# Create a Type for a List of Graph Nodes
ListNodesType = Sequence[NodeType]

# Create a dictionary - used for mapping labels to classes
LABEL_TO_CLASS = {
    "Review": Review,
    "FeedbackItem": FeedbackItem,
    "Tag": Tag,
    "Topic": Topic,
    "AppState": AppState,
}

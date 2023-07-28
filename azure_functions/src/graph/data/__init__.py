from typing import Union, Sequence
from src.graph.data.reviews import Review
from src.graph.data.feedbackItems import FeedbackItem
from src.graph.data.tags import Tag

# Create a Type for Any Graph Node
NodeType = Union[Review, FeedbackItem, Tag]

# Create a Type for a List of Graph Nodes
ListNodesType = Sequence[NodeType]

# Create a dictionary - used for mapping labels to classes
LABEL_TO_CLASS = {
    "Review": Review,
    "FeedbackItem": FeedbackItem,
    "Tag": Tag,
}

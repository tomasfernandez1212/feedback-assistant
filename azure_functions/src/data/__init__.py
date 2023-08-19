from typing import Union, Sequence, TypeVar
from src.data.reviews import Review
from src.data.feedbackItems import FeedbackItem
from src.data.observations import Observation
from src.data.topics import Topic
from src.data.state import AppState
from src.data.scores import Score
from src.data.actionItems import ActionItem


# Create a Union for all Graph Nodes
GraphNode = Union[Review, FeedbackItem, Observation, ActionItem, Score, Topic, AppState]
GraphNodeVar = TypeVar("GraphNodeVar", bound=GraphNode)

# Create a Union for all Embeddable Graph Nodes
EMBEDDABLE_CLASSES = [FeedbackItem, Observation, ActionItem, Topic]
EMBEDDABLE_CLASS_NAMES = [cls.__name__ for cls in EMBEDDABLE_CLASSES]
EmbeddableGraphNode = Union[FeedbackItem, Observation, ActionItem, Topic]
EmbeddableGraphNodeVar = TypeVar("EmbeddableGraphNodeVar", bound=EmbeddableGraphNode)


# Create a Type for a List of Graph Nodes
ListGraphNodes = Sequence[GraphNode]

# Create a dictionary - used for mapping labels to classes
LABEL_TO_CLASS = {
    "Review": Review,
    "FeedbackItem": FeedbackItem,
    "Observation": Observation,
    "Score": Score,
    "Topic": Topic,
    "AppState": AppState,
    "ActionItem": ActionItem,
}

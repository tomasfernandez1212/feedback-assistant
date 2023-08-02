from src.graph.connect import GraphConnection
from src.data import FeedbackItem
from src.data import Review
from src.data import Topic
from src.data import AppState
from src.data import DataPoint
from src.data import Score

from src.data import ListNodesType, NodeType, NodeTypeVar

from typing import List, Type
import logging

from enum import Enum


class Environment(Enum):
    TEST = 1
    PROD = 2


class Storage:
    """
    This class is used to the interface with the app's stored data.
    Whether from the eventual consistency graph, strong consistency graph, or other data stores.

    This class should be initialized with a "with" statement, so that the connections to the graph are closed properly.
    """

    def __init__(self):
        pass

    def __enter__(self):
        self.eventual_graph = GraphConnection()
        self.strong_graph = GraphConnection(strong_consistency=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):  # type: ignore
        self.eventual_graph.close()
        self.strong_graph.close()

    def _get_graph(self, node_type: type) -> GraphConnection:
        if node_type == AppState:
            return self.strong_graph
        else:
            return self.eventual_graph

    def get_node(self, id: str, type: Type[NodeTypeVar]) -> NodeTypeVar:
        return self._get_graph(type).get_node(id, type)

    def get_all_nodes_by_type(self, type: Type[NodeTypeVar]) -> List[NodeTypeVar]:
        return self._get_graph(type).get_all_nodes_by_type(type)

    def add_node(self, node: NodeType):
        self._get_graph(type(node)).add_node(node)

    def add_nodes(self, nodes: ListNodesType):
        for node in nodes:
            self.add_node(node)

    def add_edges(
        self,
        from_nodes: ListNodesType,
        to_nodes: ListNodesType,
        edge_label: str,
    ):
        graph = self._get_graph(type(from_nodes[0]))

        # Add edges to graph
        graph.add_edges(from_nodes, to_nodes, edge_label)

    def check_if_edge_exists(
        self, from_node: NodeType, to_node: NodeType, edge_label: str
    ) -> bool:
        return self._get_graph(type(from_node)).check_if_edge_exists(
            from_node, to_node, edge_label
        )

    def traverse(self, node: NodeType, edge_label: str) -> ListNodesType:
        return self._get_graph(type(node)).traverse(node, edge_label)

    def update_node(self, node: NodeType):
        self._get_graph(type(node)).update_node(node)

    def reset_storage(self, environment: Environment):
        """
        Resets the storage to a clean slate.
        """
        if environment == Environment.TEST:
            self.eventual_graph.reset_graph("feedback-assistant-test")
            self.strong_graph.reset_graph("feedback-assistant-strong-consistency-test")
        elif environment == Environment.PROD:
            self.eventual_graph.reset_graph("feedback-assistant")
            self.strong_graph.reset_graph("feedback-assistant-strong-consistency")
        else:
            raise Exception("Invalid Environment")

    def add_feedback_item(self, feedback_item: FeedbackItem, constituted_by: Review):
        """
        Adds feedback item as a node, but also adds edge to node it is constituted by.
        For now, constituted by can only be a review, but in the future it could be a messaging thread.

        Constituted by should generally be provided, but might be optional for particular testing scenarios.
        """

        self.add_node(feedback_item)
        self.add_edges([feedback_item], [constituted_by], "constituted_by")

    def add_data_point_for_feedback_item(
        self, data_point: DataPoint, feedback_item: FeedbackItem
    ):
        """
        Adds data point as node, but also adds edges between feedback item and data point.
        """

        self.add_node(data_point)
        self.add_edges([feedback_item], [data_point], "derived")
        self.add_edges([data_point], [feedback_item], "derived_from")  # reverse edge

    def add_score(self, node: NodeType, score: Score):
        """
        Adds score for node, but also adds edges between score and node being scored.
        """
        self.add_node(score)
        self.add_edges([score], [node], "scores_for")
        self.add_edges([node], [score], "scored_by")

    def add_topic_based_on_data_points(
        self, topic: Topic, data_points: List[DataPoint]
    ):
        """
        Adds topic as a node, but also adds edges between topic and data points and between feedback items and topic.
        """
        self.add_node(topic)
        self.add_edges(data_points, [topic], "belongs_to")
        self.add_edges([topic], data_points, "contains")
        for data_point in data_points:
            feedback_items = self.traverse(data_point, "derived_from")
            for feedback_item in feedback_items:
                if not self.check_if_edge_exists(feedback_item, topic, "informs"):
                    self.add_edges([feedback_item], [topic], "informs")
                    self.add_edges([topic], [feedback_item], "informed_by")

    def clear_topics(self):
        topics = self.get_all_nodes_by_type(Topic)
        for topic in topics:
            self._get_graph(Topic).delete_node(topic.id)

    def get_feedback_item_source(self, feedback_item: FeedbackItem) -> Review:
        result = self.traverse(feedback_item, "constituted_by")
        if len(result) != 1:
            raise Exception(
                f"FeedbackItem is not constituted by exactly one element. Count: {len(result)}"
            )
        return result[0]  # type: ignore

    def get_app_state(self) -> AppState:
        nodes = self.get_all_nodes_by_type(AppState)

        if len(nodes) == 0:  # type: ignore
            logging.info("No app state found in graph. Creating.")
            state = AppState()
            self.add_node(state)
            return state

        if len(nodes) > 1:
            raise Exception(
                f"More than one app state found in graph. Count: {len(nodes)}"
            )

        state = nodes[0]

        return state

    def update_app_state(self, new_app_state: AppState):
        current_app_state = self.get_app_state()

        current_app_state_dict = current_app_state.model_dump()
        new_app_state_dict = new_app_state.model_dump()

        # Find keys that exist in both dictionaries, but have different values
        changed_keys = {
            key
            for key in current_app_state_dict
            if current_app_state_dict[key] != new_app_state_dict.get(key)
        }

        if len(changed_keys) == 0:
            logging.info("No changes to app state.")
            return

        # Now, for each key in changed_keys, you can see the old and new value:
        for key in changed_keys:
            logging.info(
                f"Key {key} is getting changed from {current_app_state_dict[key]} to {new_app_state_dict[key]}"
            )

        # Update the app state in the graph
        self.update_node(new_app_state)

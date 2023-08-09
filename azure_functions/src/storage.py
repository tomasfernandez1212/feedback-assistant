from src.graph.connect import GraphConnection
from src.vector.search import VectorStore, IndexNames
from src.data import FeedbackItem
from src.data import Review
from src.data import Topic
from src.data import AppState
from src.data import DataPoint
from src.data.scores import Score, ScoreNames
from src.data import ActionItem

from src.data import ListNodesType, NodeType, NodeTypeVar

from typing import List, Type, Union, Dict, Any
import logging

from enum import Enum


class AggregationMethod(Enum):
    MEAN = "mean"
    COUNT = "count"


class Environment(Enum):
    TEST = 1
    PROD = 2


class Storage:
    """
    This class is used to the interface with the app's stored data.
    Whether from the eventual consistency graph, strong consistency graph, or other data stores such as vectorstores.

    This class should be initialized with a "with" statement, so that the connections are closed properly.
    """

    def __init__(self):
        pass

    def __enter__(self):
        self.eventual_graph = GraphConnection()
        self.strong_graph = GraphConnection(strong_consistency=True)
        self.vectorstore = VectorStore()
        return self

    def __exit__(self, exc_type, exc_value, traceback):  # type: ignore
        self.eventual_graph.close()
        self.strong_graph.close()
        for vector_client in self.vectorstore.search_clients.values():
            vector_client.close()

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
            self.vectorstore.reset("feedback-assistant-test")
        elif environment == Environment.PROD:
            self.eventual_graph.reset_graph("feedback-assistant")
            self.strong_graph.reset_graph("feedback-assistant-strong-consistency")
            self.vectorstore.reset("feedback-assistant")
        else:
            raise Exception("Invalid Environment")

    def add_feedback_item_and_source(self, feedback_item: FeedbackItem, source: Review):
        """
        Adds feedback item as a node, but also adds edge to node it is source.
        For now, source can only be a review, but in the future it could be a messaging thread.
        """

        self.add_node(source)
        self.add_node(feedback_item)
        self.add_edges([feedback_item], [source], "constituted_by")
        self.add_edges([source], [feedback_item], "constitutes")

    def add_data_point_for_feedback_item(
        self, data_point: DataPoint, feedback_item: FeedbackItem, embed: bool = True
    ):
        """
        Adds data point as node, but also adds edges between feedback item and data point.

        Optionally, embeds data point and adds to vector store.
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

    def add_action_item(self, action_item: ActionItem):
        """
        Adds action item as a node. Doesn't add any edges. This is done in a separate method.
        """
        self.add_node(action_item)

    def add_topic(self, topic: Topic):
        """
        Adds topic as a node. Doesn't add any edges. This is done in a separate method.
        """
        self.add_node(topic)

    def add_edges_for_action_item(self, action_item: ActionItem, others: ListNodesType):
        """
        Adds edges between action item and other nodes.
        """
        self.add_edges([action_item], others, "addresses")
        self.add_edges(others, [action_item], "addressed_by")

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

    def aggregate_scores_for_node(
        self,
        for_node: Union[FeedbackItem, Topic, ActionItem],
        score_name: ScoreNames,
        aggregation: AggregationMethod,
    ) -> List[Dict[str, Any]]:
        # Form query
        query = f"g.V().hasLabel({for_node.__class__.__name__}).as('x').out('addresses').hasLabel('DataPoint').out('scored_by').has('name', '{score_name.value}').values('score').group().by(select('x')).by({aggregation.value}()).unfold()"

        # Submit query
        result: List[Dict[str, float]] = self._get_graph(type(for_node)).submit_query(
            query
        )

        return result

    def add_embedding(
        self, node_id: str, node_type: Type[NodeTypeVar], embedding: List[float]
    ):
        """
        Stores the embedding of a node in the vectorstore.
        """

        try:
            index_name = IndexNames[node_type.__name__]
        except KeyError:
            raise Exception(
                f"Node type {node_type.__name__} does not have an index name defined."
            )
        self.vectorstore.add_documents(
            index_name=index_name,
            documents=[{"id": node_id, "contentVector": embedding}],
        )

    def search_with_embedding(
        self, node_type: Type[NodeTypeVar], embedding: List[float]
    ):
        """
        Searches the vectorstore for the nearest neighbors to the given embedding.
        """

        try:
            index_name = IndexNames[node_type.__name__]
        except KeyError:
            raise Exception(
                f"Node type {node_type.__name__} does not have an index name defined."
            )
        return self.vectorstore.search_with_vector(index_name, embedding, 10)

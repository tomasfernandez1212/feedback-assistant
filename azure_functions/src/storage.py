from src.graph.connect import GraphConnection
from src.vector.search import VectorStore, VectorEnv, Vector
from src.data import (
    FeedbackItem,
    Review,
    Topic,
    AppState,
    DataPoint,
    ActionItem,
    EmbeddableGraphNode,
    EmbeddableGraphNodeVar,
)
from src.data.scores import Score, ScoreNames

from src.llm.utils import generate_embedding


from src.data import ListGraphNodes, GraphNode, GraphNodeVar

from typing import List, Type, Union, Dict, Any, Tuple
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
        self.vectorstore.close()

    def _get_graph(self, node_type: type) -> GraphConnection:
        if node_type == AppState:
            return self.strong_graph
        else:
            return self.eventual_graph

    def get_node(self, id: str, type: Type[GraphNodeVar]) -> GraphNodeVar:
        return self._get_graph(type).get_node(id, type)

    def get_all_nodes_by_type(self, type: Type[GraphNodeVar]) -> List[GraphNodeVar]:
        return self._get_graph(type).get_all_nodes_by_type(type)

    def add_node(self, node: GraphNode):
        self._get_graph(type(node)).add_node(node)

    def add_nodes(self, nodes: ListGraphNodes):
        for node in nodes:
            self.add_node(node)

    def add_edges(
        self,
        from_nodes: ListGraphNodes,
        to_nodes: ListGraphNodes,
        edge_label: str,
    ):
        if len(from_nodes) == 0 or len(to_nodes) == 0:
            return

        graph = self._get_graph(type(from_nodes[0]))

        # Add edges to graph
        graph.add_edges(from_nodes, to_nodes, edge_label)

    def check_if_edge_exists(
        self, from_node: GraphNode, to_node: GraphNode, edge_label: str
    ) -> bool:
        return self._get_graph(type(from_node)).check_if_edge_exists(
            from_node, to_node, edge_label
        )

    def traverse(self, node: GraphNode, edge_label: str) -> ListGraphNodes:
        return self._get_graph(type(node)).traverse(node, edge_label)

    def update_node(self, node: GraphNode):
        self._get_graph(type(node)).update_node(node)

    def reset_storage(self, environment: Environment):
        """
        Resets the storage to a clean slate.
        """
        if environment == Environment.TEST:
            self.eventual_graph.reset_graph("feedback-assistant-test")
            self.strong_graph.reset_graph("feedback-assistant-strong-consistency-test")
            self.vectorstore.reset_env(VectorEnv.TEST)
        elif environment == Environment.PROD:
            self.eventual_graph.reset_graph("feedback-assistant")
            self.strong_graph.reset_graph("feedback-assistant-strong-consistency")
            self.vectorstore.reset_env(VectorEnv.PROD)
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
        self, data_point: DataPoint, feedback_item: FeedbackItem
    ):
        """
        Adds data point as node in graph, but also adds edges between feedback item and data point.

        Also embeds the data point and adds to vectorstore.
        """

        self.add_node(data_point)
        self.add_edges([feedback_item], [data_point], "derived")
        self.add_edges([data_point], [feedback_item], "derived_from")  # reverse edge
        self.embed_and_store(data_point)

    def add_score(self, node: GraphNode, score: Score):
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
        self.embed_and_store(action_item)

    def add_topic(self, topic: Topic):
        """
        Adds topic as a node. Doesn't add any edges. This is done in a separate method.
        """
        self.add_node(topic)
        self.embed_and_store(topic)

    def add_edges_for_action_item(
        self, action_item: ActionItem, others: ListGraphNodes
    ):
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

    def embed_and_store(self, node: EmbeddableGraphNode):
        embedding = generate_embedding(node.text)
        self.add_embeddings(
            type(node),
            [Vector(values=embedding, id=node.id)],
        )

    def add_embeddings(
        self, source_type: Type[EmbeddableGraphNodeVar], embeddings: List[Vector]
    ):
        """
        Stores the embedding of a node in the vectorstore.
        """
        self.vectorstore.add_embeddings(source_type.__name__, embeddings)

    def search_semantically(
        self,
        search_for: Type[EmbeddableGraphNodeVar],
        from_text: str,
        top_k: int,
        min_score: float = 0.0,
    ) -> Tuple[List[EmbeddableGraphNodeVar], List[float]]:
        """
        Searches the vectorstore for the nearest neighbors to the given embedding.
        """

        embedding = generate_embedding(from_text)
        matches = self.vectorstore.search_with_embedding(search_for, embedding, top_k)

        nodes: List[EmbeddableGraphNodeVar] = []
        scores: List[float] = []
        for match in matches:
            if match["score"] > min_score:
                node = self.get_node(match["id"], search_for)
                nodes.append(node)
                scores.append(match["score"])

        return nodes, scores

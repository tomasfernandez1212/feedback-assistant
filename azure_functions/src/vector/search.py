import os
from enum import Enum
from typing import List, Dict, Type

import pinecone  # type: ignore
from pinecone.core.client.models import Vector  # type: ignore
from pinecone.core.client.model.scored_vector import ScoredVector  # type: ignore

from src.data import EMBEDDABLE_CLASS_NAMES, EmbeddableGraphNodeVar


class VectorDataType(Enum):
    ActionItem = "action-items"
    Observation = "observation"
    Topic = "topics"


class VectorEnv(Enum):
    TEST = "test"
    PROD = "prod"


class VectorStore:
    def __init__(self) -> None:
        # Connect to Pinecone
        pinecone.init(  # type: ignore
            api_key=os.environ["PINECONE_API_KEY"],
            environment="asia-southeast1-gcp",
        )
        self.index_name = os.environ["PINECONE_INDEX_NAME"]
        self.index = self.get_index_object(self.index_name)
        self.default_env = VectorEnv[os.environ["PINECONE_DEFAULT_ENV"]]

        # Define All Namespaces
        self.namespaces_per_env: Dict[str, List[str]] = {}
        for environment in VectorEnv:
            env_namespaces: List[str] = []
            for embeddable_class in EMBEDDABLE_CLASS_NAMES:
                env_namespaces.append(self.get_namespace(environment, embeddable_class))
            self.namespaces_per_env[environment.value] = env_namespaces

    def get_namespace(self, environment: VectorEnv, node_class_name: str) -> str:
        """
        Get the namespace for the environment and content type.
        """
        return f"{environment.value}-{node_class_name}"

    def create_index(self, index_name: str) -> None:
        """
        Create the index on the database.
        """
        pinecone.create_index(index_name, dimension=1536)  # type: ignore

    def get_index_object(self, index_name: str) -> pinecone.Index:
        """
        Get the index objet.
        """
        return pinecone.Index(index_name)

    def delete_index(self, index_name: str) -> None:
        """
        Delete the index.
        """
        pinecone.delete_index(index_name)

    def reset_env(self, environment: VectorEnv) -> None:
        """
        Delete all documents with in the environment using namespaces.
        """

        all_namespaces = list(self.index.describe_index_stats()["namespaces"].keys())  # type: ignore
        env_namespaces = [
            namespace
            for namespace in all_namespaces
            if namespace.startswith(environment.value)
        ]
        for namespace in env_namespaces:
            self.index.delete(namespace=namespace, delete_all=True)  # type: ignore

    def search_with_embedding(
        self,
        search_for_type: Type[EmbeddableGraphNodeVar],
        vector: List[float],
        top_k: int,
    ) -> List[ScoredVector]:
        """
        Search using embedding in the index.
        """
        class_namespace = self.get_namespace(self.default_env, search_for_type.__name__)
        query_reponse = self.index.query(  # type: ignore
            namespace=class_namespace,
            vector=vector,
            top_k=top_k,
        )
        matches = query_reponse["matches"]

        return matches

    def add_embeddings(self, node_class_name: str, embeddings: List[Vector]) -> None:
        """
        Upload multiple embeddings to the index
        """
        self.index.upsert(  # type: ignore
            namespace=self.get_namespace(self.default_env, node_class_name),
            vectors=embeddings,
        )

    def close(self) -> None:
        self.index.close()

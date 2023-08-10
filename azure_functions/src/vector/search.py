import os
from enum import Enum
from typing import List, Dict

import pinecone  # type: ignore
from pinecone.core.client.models import Vector  # type: ignore


class VectorDataType(Enum):
    ActionItem = "action-items"
    DataPoint = "data-points"
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
            for vector_type in VectorDataType:
                env_namespaces.append(self.get_namespace(environment, vector_type))
            self.namespaces_per_env[environment.value] = env_namespaces

    def get_namespace(self, environment: VectorEnv, vector_type: VectorDataType) -> str:
        """
        Get the namespace for the environment and content type.
        """
        return f"{environment.value}-{vector_type.value}"

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
        for namespace in self.namespaces_per_env[environment.value]:
            self.index.delete(namespace=namespace, delete_all=True)  # type: ignore

    def search_with_embedding(
        self, vector_type: VectorDataType, vector: List[float], top_k: int
    ):
        """
        Search using embedding in the index.
        """
        query_reponse = self.index.query(  # type: ignore
            namespace=self.get_namespace(self.default_env, vector_type),
            vector=vector,
            top_k=top_k,
        )

        print(query_reponse)

    def add_embeddings(
        self, vector_type: VectorDataType, embeddings: List[Vector]
    ) -> None:
        """
        Upload multiple embeddings to the index
        """
        self.index.upsert(  # type: ignore
            namespace=self.get_namespace(self.default_env, vector_type),
            vectors=embeddings,
        )

    def close(self) -> None:
        self.index.close()

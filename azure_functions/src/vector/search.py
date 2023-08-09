import os
from enum import Enum
from typing import List, Any, Dict

import pinecone


class Namespace(Enum):
    ActionItem = "action-items"
    DataPoint = "data-points"
    Topic = "topics"


class VectorStore:
    def __init__(self) -> None:
        pinecone.init(  # type: ignore
            api_key=os.environ["PINECONE_API_KEY"],
            environment="asia-southeast1-gcp",
        )

        self.index = pinecone.Index(os.environ["PINECONE_INDEX_NAME"])  # type: ignore

    def get_index_name(self, test: bool = True) -> str:
        if test:
            return "feedback-assistant-test"
        else:
            return "feedback-assistant"

    def get_index(self, index_name: str) -> pinecone.Index:
        return self.indices[index_name]

    def initialize_index(self, index_name: str) -> None:
        """
        Create the index with the given name.
        """
        pinecone.create_index(index_name, dimension=1536)  # type: ignore
        self.indices[index_name] = pinecone.Index(index_name)  # type: ignore

    def delete_index(self, index_name: str) -> None:
        """
        Delete the index with the given name.
        """
        pinecone.delete_index(index_name)
        self.indices.pop(index_name)

    def reset(self, test_environment: bool) -> None:
        """
        Delete all documents in the indexes by deleting and recreating the indexes.
        """

        index_name = self.get_index_name(test_environment)
        self.delete_index(index_name)
        self.initialize_index(index_name)

    def search_with_vector(self, index_name: str, vector: List[float]):
        index = self.get_index(index_name)
        index.query

    def add_documents(
        self, index_name: Namespace, documents: List[Dict[Any, Any]]
    ) -> None:
        """
        Upload multiple documents to the index
        """
        client = self.get_client(index_name)
        result = client.upload_documents(documents=documents)  # type: ignore

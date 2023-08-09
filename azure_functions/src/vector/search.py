import os
from enum import Enum
from typing import List, Any, Dict
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient, SearchItemPaged
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchField,
    SearchableField,
    SearchFieldDataType,
    VectorSearch,
    HnswVectorSearchAlgorithmConfiguration,
)
from azure.search.documents.models import Vector


class IndexNames(Enum):
    ActionItem = "action-items"
    DataPoint = "data-points"
    Topic = "topics"


class VectorStore:
    def __init__(self) -> None:
        credential = AzureKeyCredential(os.environ["COG_API_KEY"])
        self.search_clients: Dict[IndexNames, SearchClient] = {}
        self.store_name = os.environ["COG_SEARCH_NAME"]
        self.store_endpoint = f"https://{self.store_name}.search.windows.net/"

        self.search_index_client = SearchIndexClient(
            endpoint=self.store_endpoint,
            credential=credential,
        )

        for index_name in IndexNames:
            search_client = SearchClient(
                endpoint=self.store_endpoint,
                index_name=index_name.value,
                credential=credential,
            )
            self.search_clients[index_name] = search_client

    def initialize_index(self, index_name: IndexNames) -> None:
        """
        Create the index with the given name.
        """
        self.search_index_client.create_index(
            SearchIndex(
                name=index_name.value,
                fields=[
                    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                    SearchableField(
                        name="contentVector",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True,
                        vector_search_dimensions=1536,
                        vector_search_configuration="my-vector-config",
                    ),
                ],
                vector_search=VectorSearch(
                    algorithm_configurations=[
                        HnswVectorSearchAlgorithmConfiguration(name="my-vector-config")
                    ]
                ),
            )
        )

    def reset(self, confirm_store_name: str) -> None:
        """
        Delete all documents in the indexes by deleting and recreating the indexes.
        """
        if confirm_store_name != self.store_name:
            raise Exception("Vectorstore name does not match")

        for index_name in IndexNames:
            self.search_index_client.delete_index(index_name.value)
            self.initialize_index(index_name)

    def get_client(self, index_name: IndexNames) -> SearchClient:
        return self.search_clients[index_name]

    def search_with_vector(
        self, index_name: IndexNames, vector: List[float], topk: int = 3
    ) -> SearchItemPaged[Dict[Any, Any]]:
        client = self.get_client(index_name)
        result = client.search(  # type: ignore
            search_text="",
            vectors=[Vector(value=vector, k=topk, fields="contentVector")],
            select=["id"],
        )
        return result  # type: ignore

    def add_documents(
        self, index_name: IndexNames, documents: List[Dict[Any, Any]]
    ) -> None:
        """
        Upload multiple documents to the index
        """
        client = self.get_client(index_name)
        result = client.upload_documents(documents=documents)  # type: ignore

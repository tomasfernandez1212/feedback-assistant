import os
from enum import Enum
from typing import List, Any, Dict
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient, SearchItemPaged


class IndexNames(Enum):
    ActionItem = "action-items"
    DataPoint = "data-points"
    Topic = "topics"


class VectorSearch:
    def __init__(self) -> None:
        credential = AzureKeyCredential(os.environ["COG_API_KEY"])

        for index_name in IndexNames:
            client = SearchClient(
                endpoint=os.environ["COG_SEARCH_ENDPOINT"],
                index_name=index_name.value,
                credential=credential,
            )
            setattr(self, f"client_{index_name.value.replace('-', '_')}", client)

    def get_client(self, index_name: IndexNames) -> SearchClient:
        return getattr(self, f"client_{index_name.value.replace('-', '_')}")

    def search_with_vector(
        self, index_name: IndexNames, vector: List[float]
    ) -> SearchItemPaged[Dict[Any, Any]]:
        client = self.get_client(index_name)
        result = client.search(  # type: ignore
            search_text="",
            vector=vector,
            topk=3,
            vector_fields="contentVector",
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
        client.upload_documents(documents=documents)  # type: ignore

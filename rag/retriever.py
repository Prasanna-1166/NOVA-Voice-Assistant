from typing import List, Optional
from rag.embedding_service import EmbeddingService
from rag.vector_store import LocalVectorStore
from rag.document_models import RetrievedChunk


class Retriever:
    """
    Retrieves and ranks relevant document chunks for a given query.
    """

    def __init__(self, vector_store: LocalVectorStore, embedding_service: EmbeddingService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def retrieve(self, query: str, top_k: int = 4, threshold: float = 0.25) -> List[RetrievedChunk]:
        query_emb = self.embedding_service.generate_embedding(query)
        if not query_emb:
            return []
        return self.vector_store.search(query_emb, top_k=top_k, threshold=threshold)
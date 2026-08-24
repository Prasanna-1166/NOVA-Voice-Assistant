import unittest
from unittest.mock import MagicMock
from rag.retriever import Retriever
from rag.document_models import DocumentChunk, RetrievedChunk


class TestRetriever(unittest.TestCase):
    def test_retrieve(self):
        mock_store = MagicMock()
        mock_emb = MagicMock()
        mock_emb.generate_embedding.return_value = [0.1, 0.2]
        
        chunk = DocumentChunk(document_id="d1", chunk_index=0, text="Sample context", source_filename="file.txt")
        mock_store.search.return_value = [RetrievedChunk(chunk=chunk, similarity_score=0.9)]

        retriever = Retriever(mock_store, mock_emb)
        results = retriever.retrieve("query text")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk.text, "Sample context")


if __name__ == "__main__":
    unittest.main()
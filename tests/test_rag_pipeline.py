import unittest
from unittest.mock import MagicMock
from rag.rag_pipeline import RAGPipeline


class TestRAGPipeline(unittest.TestCase):
    def test_query_no_context(self):
        mock_store = MagicMock()
        mock_store.search.return_value = []
        mock_emb = MagicMock()
        mock_emb.generate_embedding.return_value = [0.1]

        pipeline = RAGPipeline(vector_store=mock_store, embedding_service=mock_emb)
        res = pipeline.query("What is quantum computing?")
        self.assertIn("couldn't find enough relevant information", res)


if __name__ == "__main__":
    unittest.main()
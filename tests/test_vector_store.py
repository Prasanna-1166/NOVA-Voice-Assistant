import unittest
import tempfile
from pathlib import Path
from rag.vector_store import LocalVectorStore
from rag.document_models import DocumentChunk


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_path = Path(self.temp_dir.name) / "vector_store.json"
        self.store = LocalVectorStore(storage_path=self.store_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_search(self):
        chunk = DocumentChunk(document_id="doc1", chunk_index=0, text="Deadlock prevention", source_filename="os.txt")
        self.store.add_chunks([chunk], [[1.0, 0.0, 0.0]])

        results = self.store.search([1.0, 0.0, 0.0], top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk.text, "Deadlock prevention")

    def test_delete_document(self):
        chunk = DocumentChunk(document_id="doc1", chunk_index=0, text="Text", source_filename="os.txt")
        self.store.add_chunks([chunk], [[1.0, 0.0]])
        self.assertTrue(self.store.delete_document("os.txt"))
        self.assertEqual(len(self.store.list_documents()), 0)


if __name__ == "__main__":
    unittest.main()
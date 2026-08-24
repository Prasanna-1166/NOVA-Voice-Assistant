import unittest
from rag.document_models import Document
from rag.text_chunker import TextChunker


class TestTextChunker(unittest.TestCase):
    def test_chunking_text(self):
        content = " ".join([f"Word{i}" for i in range(1200)])
        doc = Document(filename="test.txt", source_path="/test.txt", file_type="txt", content=content)
        chunker = TextChunker(chunk_size=500, overlap=50)
        chunks = chunker.chunk_document(doc)
        
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].chunk_index, 0)
        self.assertEqual(chunks[0].source_filename, "test.txt")


if __name__ == "__main__":
    unittest.main()
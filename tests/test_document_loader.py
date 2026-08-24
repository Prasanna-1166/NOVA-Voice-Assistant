import unittest
import tempfile
from pathlib import Path
from rag.document_loader import DocumentLoader


class TestDocumentLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.txt_path = Path(self.temp_dir.name) / "sample.txt"
        with open(self.txt_path, "w", encoding="utf-8") as f:
            f.write("Operating Systems handle deadlocks through detection and prevention.")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_txt(self):
        doc = DocumentLoader.load_document(str(self.txt_path))
        self.assertEqual(doc.filename, "sample.txt")
        self.assertIn("deadlocks", doc.content)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            DocumentLoader.load_document("non_existent_file.txt")

    def test_unsupported_extension_raises(self):
        bad_file = Path(self.temp_dir.name) / "sample.exe"
        bad_file.touch()
        with self.assertRaises(ValueError):
            DocumentLoader.load_document(str(bad_file))


if __name__ == "__main__":
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
from rag.embedding_service import EmbeddingService


class TestEmbeddingService(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_generate_embedding(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"embedding": [0.1, 0.2, 0.3]}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        service = EmbeddingService()
        vec = service.generate_embedding("test query")
        self.assertEqual(vec, [0.1, 0.2, 0.3])


if __name__ == "__main__":
    unittest.main()
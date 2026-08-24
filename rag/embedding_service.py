import json
import urllib.request
import urllib.error
from typing import List, Optional


class EmbeddingService:
    """
    Local embedding generator calling Ollama's /api/embeddings or /api/embed endpoints.
    Uses 'nomic-embed-text' model by default.
    """

    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "nomic-embed-text"):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            return []

        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.model_name, "prompt": text}
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    return res_json.get("embedding", [])
                raise RuntimeError(f"Ollama returned HTTP status {resp.status}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding via Ollama: {str(e)}")

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self.generate_embedding(t) for t in texts]
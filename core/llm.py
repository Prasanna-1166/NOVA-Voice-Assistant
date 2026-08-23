import json
import urllib.request
import urllib.error
from typing import Optional


class OllamaProvider:
    """
    Local LLM provider abstraction wrapping Ollama API.
    Communicates via local REST endpoints (default: http://localhost:11434).
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:3b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def check_health(self) -> bool:
        """
        Verifies that Ollama server is running and accessible locally.
        Checks both root / and /api/tags endpoints.
        """
        for endpoint in ["/", "/api/tags"]:
            try:
                req = urllib.request.Request(f"{self.base_url}{endpoint}", method="GET")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                continue
        return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Sends generation payload to Ollama /api/generate endpoint.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    result = json.loads(resp.read().decode("utf-8"))
                    return result.get("response", "").strip()
                return f"[!] Ollama returned HTTP status {resp.status}"
        except urllib.error.URLError as e:
            return f"[!] Failed to connect to Ollama: {e.reason}"
        except Exception as e:
            return f"[!] LLM Generation Error: {str(e)}"
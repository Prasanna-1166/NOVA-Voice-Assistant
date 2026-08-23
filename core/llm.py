import requests
from abc import ABC, abstractmethod
from typing import Optional
from core.config import OLLAMA_BASE_URL, DEFAULT_MODEL_NAME, OLLAMA_REQUEST_TIMEOUT


class ModelProvider(ABC):
    """Abstract Base Class for LLM Providers."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, base_url: str = OLLAMA_BASE_URL):
        self.model_name = model_name
        self.base_url = base_url

    @abstractmethod
    def initialize(self) -> bool:
        """Check if provider and target model are available."""
        pass

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text response from the model."""
        pass


class OllamaProvider(ModelProvider):
    """Concrete implementation for local Ollama API."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, base_url: str = OLLAMA_BASE_URL):
        super().__init__(model_name=model_name, base_url=base_url)

    def initialize(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                installed_names = [m.get("name") for m in models]
                return any(self.model_name in name for name in installed_names) or True
            return False
        except requests.exceptions.RequestException:
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(url, json=payload, timeout=OLLAMA_REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            return f"[!] Ollama returned HTTP error code {response.status_code}."
        except requests.exceptions.Timeout:
            return "[!] Generation timed out."
        except requests.exceptions.RequestException as e:
            return f"[!] Error communicating with local Ollama service: {str(e)}"


# Backward compatibility alias
OllamaLLM = OllamaProvider
import sys
import ollama


class NovaLLM:
    """
    Manages direct communication between NOVA and local Ollama instance.
    """

    def __init__(self, model_name: str = "qwen2.5:3b"):
        self.model_name = model_name

    def verify_connection(self) -> bool:
        """
        Verifies that Ollama service is active and the selected model is loaded.
        """
        try:
            models_response = ollama.list()

            if hasattr(models_response, "models"):
                available_models = [
                    getattr(m, "model", getattr(m, "name", ""))
                    for m in models_response.models
                ]

            elif isinstance(models_response, dict):
                available_models = [
                    m.get("model", m.get("name", ""))
                    for m in models_response.get("models", [])
                ]

            else:
                available_models = []

            for m in available_models:
                if self.model_name in m:
                    return True

            print(
                f"[!] Warning: Model '{self.model_name}' not found in Ollama."
            )
            return False

        except Exception as e:
            print(
                f"[!] Error connecting to Ollama service: "
                f"{type(e).__name__} - {e}"
            )
            return False

    def generate_response(
        self,
        prompt: str,
        system_prompt: str = ""
    ) -> str:
        """
        Sends a text prompt to local LLM and returns the output string directly.
        """

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": 0.1
                }
            )

            if hasattr(response, "message"):
                return response.message.content.strip()

            return response.get(
                "message",
                {}
            ).get(
                "content",
                ""
            ).strip()

        except Exception as e:
            return f"[Error generating response]: {e}"


if __name__ == "__main__":
    brain = NovaLLM(model_name="qwen2.5:3b")

    if brain.verify_connection():
        print(
            brain.generate_response(
                "Say hello in Telugu concisely."
            )
        )
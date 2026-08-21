import ollama
from datetime import datetime

class NovaAssistant:
    """
    Handles conversation logic with the local Ollama LLM engine.
    """
    def __init__(self, model_name: str = "qwen2.5:3b"):
        self.model_name = model_name
        # Persona enforcing 'Boss' address and concise output for speech speed
        self.system_prompt = (
            "You are NOVA, an executive AI personal assistant. "
            "You must ALWAYS address the user as 'Boss' in EVERY response without fail. "
            "Keep your answers short, natural, and direct (1 to 2 sentences maximum)."
        )

    def initialize(self) -> bool:
        try:
            ollama.list()
            return True
        except Exception as e:
            print(f"[!] Ollama Connection Error: {e}")
            return False

    def process_message(self, user_message: str) -> str:
        now = datetime.now()
        current_date_str = now.strftime("%A, %B %d, %Y")
        current_time_str = now.strftime("%I:%M %p")

        prompt_with_context = (
            f"[SYSTEM CONTEXT: Today's Date is {current_date_str}. Current Time is {current_time_str}.]\n"
            f"User Question: {user_message}"
        )

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt_with_context}
                ]
            )
            return response['message']['content'].strip()
        except Exception as e:
            return f"I encountered an error processing your request, Boss: {e}"
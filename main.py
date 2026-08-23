import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import sys
import time
import threading
import queue

from core.assistant import NovaAssistant
from core.intent_router import InputSource
from voice.stt import NovaSTT
from voice.tts import NovaTTS
from voice.wakeword import NovaWakeWord


class NovaVoicePipeline:
    def __init__(self):
        print("==========================================")
        print("          NOVA Voice Assistant            ")
        print("==========================================")
        
        self.assistant = NovaAssistant()
        self.stt = NovaSTT(model_size="tiny.en")
        self.tts = NovaTTS(voice="en-GB-SoniaNeural")
        self.wakeword = NovaWakeWord(target_model="alexa", threshold=0.5)
        self.input_queue = queue.Queue()

    def boot(self):
        print("\n[*] Booting NOVA Core Subsystems...")
        
        # Verify Ollama connection with fallback warning
        if not self.assistant.initialize():
            print("[⚠️ Warning]: Ollama service not detected at http://localhost:11434.")
            print("[⚠️ Warning]: LLM reasoning fallback disabled. Deterministic tools & task memory remain ACTIVE.")
        else:
            print("[✓] Ollama Local LLM Connected.")

        print("[✓] All Subsystems Online and Ready.\n")
        
        startup_msg = "NOVA systems online Boss. Listening for Alexa or text input."
        print(f"[🗣️ NOVA]: {startup_msg}\n")
        self.tts.speak(startup_msg)

    def keyboard_listener(self):
        """Background thread to capture typed user input in terminal."""
        while True:
            try:
                text = input()
                if text.strip():
                    self.input_queue.put(("text", text.strip()))
            except EOFError:
                break

    def process_command(self, user_text: str, source: str = "text"):
        """Processes any command coming from voice or text."""
        if not user_text or len(user_text.strip()) == 0:
            return

        if source == "voice":
            print(f"\n[👤 User (Voice)]: {user_text}")

        # Termination commands
        if user_text.lower() in ["exit", "stop", "quit", "goodbye nova", "bye nova"]:
            self.tts.speak("Shutting down voice engine. Goodbye Boss.")
            print("\n[✓] NOVA Session Terminated Cleanly.")
            os._exit(0)

        input_src = InputSource.VOICE if source == "voice" else InputSource.TEXT

        print("[🧠 NOVA]: Processing...")
        response_text = self.assistant.process_turn(user_text, source=input_src)
        
        print(f"[🗣️ NOVA]: {response_text}\n")
        self.tts.speak(response_text)

    def run_pipeline(self):
        self.boot()

        # Start keyboard listener thread
        kb_thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        kb_thread.start()

        print("-----------------------------------------------------------")
        print(" [🎙️ VOICE]: Say 'ALEXA' to speak.")
        print(" [⌨️ TEXT]: Type any command in this console and press Enter.")
        print("-----------------------------------------------------------\n")

        try:
            while True:
                # 1. Process keyboard inputs
                if not self.input_queue.empty():
                    src, text = self.input_queue.get()
                    self.process_command(text, source=src)
                    continue

                # 2. Check wake-word
                if self.wakeword.check_wake_word_step():
                    self.tts.speak("Yes?")
                    audio_file = self.stt.record_audio(record_seconds=5)
                    
                    if audio_file:
                        user_text = self.stt.transcribe(audio_file, language="en")
                        if user_text and user_text.strip():
                            self.process_command(user_text, source="voice")

                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n[!] Emergency Stop Triggered by User.")
            self.tts.speak("Shutting down Boss.")


if __name__ == "__main__":
    pipeline = NovaVoicePipeline()
    pipeline.run_pipeline()
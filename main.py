import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import sys
import time
import threading
import queue

from core.assistant import NovaAssistant
from core.intent_router import InputSource


class DummyTTS:
    """Fallback TTS engine when TTS initialization fails."""
    def speak(self, text: str):
        pass


class NovaVoicePipeline:
    def __init__(self):
        print("==========================================")
        print("          NOVA Voice & Text Assistant     ")
        print("==========================================")
        
        self.assistant = NovaAssistant()
        self.input_queue = queue.Queue()

        # 1. Independent TTS Setup (Spoken Output)
        try:
            from voice.tts import NovaTTS
            self.tts = NovaTTS(voice="en-GB-SoniaNeural")
            self.tts_enabled = True
            print("[✓] TTS Voice Engine Active (Output Ready).")
        except Exception as e:
            print(f"[⚠️ Warning]: TTS Output engine failed ({e}). Falling back to Silent Mode.")
            self.tts = DummyTTS()
            self.tts_enabled = False

        # 2. Independent Wake Word & STT Setup (Mic Input)
        try:
            from voice.stt import NovaSTT
            from voice.wakeword import NovaWakeWord
            self.stt = NovaSTT(model_size="tiny.en")
            self.wakeword = NovaWakeWord(target_model="alexa", threshold=0.5)
            self.mic_enabled = True
            print("[✓] Microphone & Wake Word Active (Input Ready).")
        except Exception as e:
            print(f"[⚠️ Warning]: Wake word / STT disabled due to DLL restriction: {e}")
            print("[ℹ️ Info]: Keyboard Input Mode Active.")
            self.mic_enabled = False

    def boot(self):
        print("\n[*] Booting NOVA Core Subsystems...")
        
        # Verify Ollama connection with fallback warning
        if not self.assistant.initialize():
            print("[⚠️ Warning]: Ollama service not detected at http://localhost:11434.")
            print("[⚠️ Warning]: LLM reasoning fallback disabled. Deterministic tools & task memory remain ACTIVE.")
        else:
            print("[✓] Ollama Local LLM Connected.")

        print("[✓] All Subsystems Online and Ready.\n")
        
        startup_msg = "NOVA systems online Boss. Ready for multi-step agent requests."
        print(f"[🗣️ NOVA]: {startup_msg}\n")
        if self.tts_enabled:
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
            if self.tts_enabled:
                self.tts.speak("Shutting down engine. Goodbye Boss.")
            print("\n[✓] NOVA Session Terminated Cleanly.")
            os._exit(0)

        input_src = InputSource.VOICE if source == "voice" else InputSource.TEXT

        print("[🧠 NOVA]: Processing...")
        response_text = self.assistant.process_turn(user_text, source=input_src)
        
        print(f"[🗣️ NOVA]: {response_text}\n")
        if self.tts_enabled:
            self.tts.speak(response_text)

    def run_pipeline(self):
        self.boot()

        # Start keyboard listener thread
        kb_thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        kb_thread.start()

        print("-----------------------------------------------------------")
        if self.mic_enabled:
            print(" [🎙️ VOICE]: Say 'ALEXA' to speak.")
        else:
            print(" [🎙️ VOICE]: Microphone Disabled (DLL Blocked)")
        print(" [🔊 AUDIO]: Voice Output ACTIVE")
        print(" [⌨️ TEXT]: Type any command in this console and press Enter.")
        print("-----------------------------------------------------------\n")

        try:
            while True:
                # 1. Process keyboard inputs
                if not self.input_queue.empty():
                    src, text = self.input_queue.get()
                    self.process_command(text, source=src)
                    continue

                # 2. Check wake-word (only if mic/wakeword is enabled)
                if self.mic_enabled and hasattr(self, 'wakeword'):
                    if self.wakeword.check_wake_word_step():
                        if self.tts_enabled:
                            self.tts.speak("Yes?")
                        audio_file = self.stt.record_audio(record_seconds=5)
                        
                        if audio_file:
                            user_text = self.stt.transcribe(audio_file, language="en")
                            if user_text and user_text.strip():
                                self.process_command(user_text, source="voice")

                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n[!] Emergency Stop Triggered by User.")
            if self.tts_enabled:
                self.tts.speak("Shutting down Boss.")


if __name__ == "__main__":
    pipeline = NovaVoicePipeline()
    pipeline.run_pipeline()
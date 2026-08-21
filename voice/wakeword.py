import openwakeword
import numpy as np
import sounddevice as sd

class NovaWakeWord:
    def __init__(self, target_model: str = "alexa", threshold: float = 0.5):
        print("[*] Initializing Wake-Word Engine...")
        self.target_model = target_model
        self.threshold = threshold
        
        # Download and load the openwakeword model
        openwakeword.utils.download_models()
        self.oww_model = openwakeword.Model(
            wakeword_models=[target_model], 
            inference_framework="onnx"
        )
        
        # Audio configuration
        self.chunk_size = 1280
        self.sample_rate = 16000
        
        # Start sounddevice InputStream
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self.chunk_size
        )
        self.stream.start()
        print(f"[✓] Wake-Word Engine Active (Listening for '{target_model}').")

    def check_wake_word_step(self) -> bool:
        """
        Non-blocking check for a single frame of audio to see if wake-word is triggered.
        Returns True if threshold is met.
        """
        try:
            # Read chunk from sounddevice stream
            audio_data, _ = self.stream.read(self.chunk_size)
            audio_data = audio_data.flatten()
            
            # Predict wake word confidence score
            prediction = self.oww_model.predict(audio_data)
            score = prediction.get(self.target_model, 0.0)

            if score >= self.threshold:
                print(f"\n[⚡ WAKE]: Wake-Word Detected! (Score: {score:.2f})")
                self.oww_model.reset()
                return True
            return False
        except Exception:
            return False

    def listen_for_wake_word(self):
        """
        Blocking loop fallback.
        """
        print(f"\n[💤 IDLE]: Say '{self.target_model.upper()}' to activate...")
        while True:
            if self.check_wake_word_step():
                break

    def close(self):
        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass
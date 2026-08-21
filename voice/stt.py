import io
import wave
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

class NovaSTT:
    def __init__(self, model_size: str = "tiny.en", device: str = "cpu", compute_type: str = "int8"):
        print(f"[*] Loading Whisper STT model ('{model_size}' on {device})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("[✓] Whisper STT Model Loaded Successfully.")
        
        self.sample_rate = 16000
        self.channels = 1

    def record_audio(self, record_seconds: int = 5) -> bytes:
        print("[🎙️ LISTENING...]: Speak your command...")
        
        try:
            audio_data = sd.rec(
                int(record_seconds * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=self.channels, 
                dtype='int16'
            )
            sd.wait()

            wav_buffer = io.BytesIO()
            wf = wave.open(wav_buffer, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
            wav_buffer.seek(0)

            return wav_buffer.read()
            
        except Exception as e:
            print(f"[!] Recording Error: {e}")
            return b""

    def transcribe(self, audio_data: bytes, language: str = "en") -> str:
        if not audio_data:
            return ""

        try:
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Context hint improves command recognition accuracy dramatically
            initial_prompt = "Voice assistant commands: open Chrome, take screenshot, change volume, what time is it."
            
            segments, _ = self.model.transcribe(
                audio_np, 
                beam_size=3,  # Increased beam_size from 1 to 3 for higher accuracy
                language=language,
                initial_prompt=initial_prompt
            )
            transcription = " ".join([segment.text for segment in segments]).strip()
            return transcription
        except Exception as e:
            print(f"[!] STT Transcription Error: {e}")
            return ""

WhisperSTT = NovaSTT
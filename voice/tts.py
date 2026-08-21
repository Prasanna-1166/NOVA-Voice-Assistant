import edge_tts
import asyncio
import pygame
import os
import uuid

class NovaTTS:
    def __init__(self, voice="en-GB-SoniaNeural"):
        self.voice = voice
        pygame.mixer.init()

    async def _generate_audio(self, text: str, output_file: str):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_file)

    def speak(self, text: str):
        if not text or not text.strip():
            return

        # Unique filename prevents [Errno 13] file lock errors
        filename = f"nova_speech_{uuid.uuid4().hex[:6]}.mp3"
        try:
            asyncio.run(self._generate_audio(text, filename))
            
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[!] TTS Execution Error: {e}")
        finally:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass
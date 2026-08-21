import asyncio
import edge_tts
import pygame
import os

# "en-US-AnaNeural" is a sweet, warm female voice option
VOICE = "en-US-AnaNeural"
TEXT = "Hello! I am NOVA, your local assistant. Systems are fully functional."
OUTPUT_FILE = "response.mp3"

async def generate_audio():
    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save(OUTPUT_FILE)

def play_audio():
    pygame.mixer.init()
    pygame.mixer.music.load(OUTPUT_FILE)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()
    
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

if __name__ == "__main__":
    print("[*] Generating neural voice stream...")
    asyncio.run(generate_audio())
    print("[🗣️ NOVA]: Speaking...")
    play_audio()
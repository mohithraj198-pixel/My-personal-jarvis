import os
import sys
import time
import threading
import asyncio
import warnings
from typing import Union

# Suppress pygame welcome message and pkg_resources deprecation warning
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    import pygame
except ImportError:
    pygame = None

try:
    import win32com.client
except ImportError:
    win32com = None

def print_animated_message(message):
    for char in message:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.030)
    print()

async def _edge_tts_speak(message: str, voice: str, file_path: str):
    communicate = edge_tts.Communicate(message, voice)
    await communicate.save(file_path)

def Co_speak(message: str, voice: str = "en-GB-RyanNeural", folder: str = "", extension: str = ".mp3") -> Union[None, str]:
    if not message or not str(message).strip():
        return None

    message = str(message).strip()
    file_path = os.path.join(folder, f"speech_temp_{int(time.time() * 1000)}{extension}")
    played = False

    # Try high-quality neural voice via edge-tts first
    if edge_tts and pygame:
        try:
            # Map legacy names if passed
            if voice in ["Matthew", "Brian", "default"] or not ("-" in voice):
                voice = "en-GB-RyanNeural"

            asyncio.run(_edge_tts_speak(message, voice, file_path))
            if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
                pygame.mixer.init()
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                pygame.mixer.quit()
                played = True
        except Exception as e:
            played = False

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

    # Offline fallback via Windows SAPI.SpVoice
    if not played and win32com:
        try:
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(message)
            played = True
        except Exception as e:
            print(f"TTS fallback error: {e}")

    return None

def speak(text):
    t1 = threading.Thread(target=Co_speak, args=(text,))
    t2 = threading.Thread(target=print_animated_message, args=(text,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
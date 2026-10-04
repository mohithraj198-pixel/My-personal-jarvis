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
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None

# Single speech queue lock to prevent overlapping voice output
_speech_lock = threading.Lock()
_is_speaking_flag = False
_last_speech_time = 0.0

def is_speaking() -> bool:
    """Return True if TTS is actively speaking or in post-speech echo grace period."""
    global _is_speaking_flag, _last_speech_time
    if _is_speaking_flag:
        return True
    if (time.time() - _last_speech_time) < 0.6:
        return True
    return False

def get_last_speech_time() -> float:
    global _last_speech_time
    return _last_speech_time

def print_animated_message(message: str):
    """Safely print text with typewriter animation effect."""
    try:
        for char in str(message):
            try:
                sys.stdout.write(char)
                sys.stdout.flush()
            except Exception:
                pass
            time.sleep(0.015)
        print()
    except Exception:
        try:
            print(str(message))
        except Exception:
            pass

async def _edge_tts_speak(message: str, voice: str, file_path: str):
    communicate = edge_tts.Communicate(message, voice)
    await communicate.save(file_path)

def Co_speak(message: str, voice: str = "en-GB-RyanNeural", folder: str = "", extension: str = ".mp3") -> Union[None, str]:
    global _is_speaking_flag, _last_speech_time
    if not message or not str(message).strip():
        return None

    message = str(message).strip()
    file_path = os.path.join(folder, f"speech_temp_{int(time.time() * 1000)}_{os.getpid()}{extension}")
    played = False

    with _speech_lock:
        _is_speaking_flag = True
        try:
            # 1. Try high-quality neural voice via edge-tts first
            if edge_tts and pygame:
                try:
                    if voice in ["Matthew", "Brian", "default"] or not ("-" in voice):
                        voice = "en-GB-RyanNeural"

                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Create new loop in separate thread if already running
                            new_loop = asyncio.new_event_loop()
                            new_loop.run_until_complete(_edge_tts_speak(message, voice, file_path))
                            new_loop.close()
                        else:
                            loop.run_until_complete(_edge_tts_speak(message, voice, file_path))
                    except Exception:
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

            # 2. Reliable offline fallback via Windows SAPI.SpVoice with COM initialization
            if not played and win32com and pythoncom:
                try:
                    pythoncom.CoInitialize()
                    try:
                        speaker = win32com.client.Dispatch("SAPI.SpVoice")
                        speaker.Speak(message)
                        played = True
                    finally:
                        pythoncom.CoUninitialize()
                except Exception as e:
                    print(f"[Jarvis - TTS Error]: SAPI fallback failed: {e}")
        finally:
            _is_speaking_flag = False
            _last_speech_time = time.time()

    return None

def speak(text: str):
    """Speak text aloud using thread-safe serialized TTS."""
    global _is_speaking_flag, _last_speech_time
    if not text or not str(text).strip():
        return
    _is_speaking_flag = True
    try:
        t1 = threading.Thread(target=Co_speak, args=(text,))
        t2 = threading.Thread(target=print_animated_message, args=(text,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    finally:
        _is_speaking_flag = False
        _last_speech_time = time.time()

if __name__ == "__main__":
    speak("Hello sir, speech system is online.")
import os
import re
from dotenv import load_dotenv

load_dotenv()

try:
    from webscout import FreeAI, Toolbaz
except ImportError:
    FreeAI = None
    Toolbaz = None

def clean_brain_text(text: str) -> str:
    """Clean markdown, emojis, and special characters for voice and Windows console."""
    if not text:
        return ""
    # Strip markdown formatting
    cleaned = re.sub(r'[*_#`~]', '', text)
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
    # Strip non-ASCII/emojis that fail on Windows charmap console and TTS
    cleaned = re.sub(r'[^\x00-\x7F]+', ' ', cleaned)
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

class PhindSearch:
    """Backward compatibility wrapper for legacy PhindSearch calls."""
    def __init__(self, *args, **kwargs):
        pass

    def chat(self, text: str) -> str:
        return Main_Brain(text)

def _extract_text_from_ai_response(res) -> str:
    """Safely extract string content from various provider response types."""
    if not res:
        return ""
    if isinstance(res, str):
        return res
    if isinstance(res, dict):
        for key in ["text", "response", "content", "message", "answer"]:
            if key in res and isinstance(res[key], str):
                return res[key]
    if hasattr(res, "__iter__"):
        try:
            return "".join(str(chunk) for chunk in res)
        except Exception:
            pass
    return str(res)

def Main_Brain(text: str, allow_groq: bool = True) -> str:
    """
    Main brain inference for Jarvis.
    1. Tries high-speed Groq AI first if available (and not in fallback mode).
    2. Falls back to FreeAI / Toolbaz webscout providers.
    3. Returns a clean, sanitized voice-friendly response.
    """
    if not text or not str(text).strip():
        return "I am online and ready to assist you, sir."

    cleaned_query = str(text).strip()
    # Strip wake words if user said 'jarvis' or 'hey jarvis'
    cleaned_query = re.sub(r'^(?:hey\s+|hello\s+|hi\s+|ok\s+)?jarvis[,:\s]*', '', cleaned_query, flags=re.IGNORECASE).strip()
    if not cleaned_query:
        cleaned_query = str(text).strip()

    # 1. Try Groq if key exists and allow_groq is enabled
    if allow_groq and os.environ.get("GROQ_API_KEY", "").strip():
        try:
            from groq_service import ask_groq
            groq_res = ask_groq(cleaned_query, stream=False)
            if groq_res and groq_res.strip() and not groq_res.startswith("Sorry, I encountered a temporary connection issue"):
                return clean_brain_text(groq_res)
        except Exception:
            pass

    # 2. Resilient Fallback: webscout FreeAI
    if FreeAI:
        try:
            ai = FreeAI()
            raw_res = ai.chat(cleaned_query)
            extracted = _extract_text_from_ai_response(raw_res)
            cleaned = clean_brain_text(extracted)
            if cleaned:
                return cleaned
        except Exception:
            pass

    # 3. Resilient Fallback: webscout Toolbaz
    if Toolbaz:
        try:
            ai = Toolbaz()
            raw_res = ai.chat(cleaned_query)
            extracted = _extract_text_from_ai_response(raw_res)
            cleaned = clean_brain_text(extracted)
            if cleaned:
                return cleaned
        except Exception:
            pass

    return "I am online and ready to assist you, sir."


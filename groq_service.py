import os
import sys
import re
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
except ImportError:
    Groq = None

# Default Groq settings configurable via .env
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b").strip()
try:
    MAX_HISTORY = int(os.environ.get("MAX_HISTORY", 12))
except Exception:
    MAX_HISTORY = 12

SYSTEM_PROMPT = """You are Jarvis, a fast, helpful, intelligent voice assistant.
Strict rules:
1. Always focus strictly on the user's latest query. Answer the specific question directly.
2. NEVER repeat previous answers, old topics, or previous conversation unless the user explicitly asks a follow-up referring to them (such as 'he', 'it', 'that', 'the previous one').
3. Keep answers concise, natural, and direct (1 to 2 sentences for voice) unless the user asks for code, a list, or detailed explanation.
4. Do not generate unsolicited extra advice, unasked follow-up offers, or tangential information.
5. Never claim to have performed a computer action (like opening an app or sending a message) unless confirmed.
6. Do not use markdown like asterisks, bullet points, or bold text in your speech."""

# Global state for multi-turn conversation memory and client
_client = None
_conversation_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def safe_print(msg: str):
    """Safely print text to Windows console without encoding exceptions."""
    try:
        print(msg, end="", flush=True)
    except Exception:
        try:
            print(str(msg).encode("ascii", errors="replace").decode("ascii"), end="", flush=True)
        except Exception:
            pass

def reload_env():
    """Reload environment variables from .env files in script directory and CWD."""
    env_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    ]
    for p in env_paths:
        if os.path.exists(p):
            try:
                load_dotenv(p, override=True)
            except Exception:
                pass

reload_env()

def get_groq_client():
    """Initialize Groq client once and reuse."""
    global _client
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        reload_env()
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        return None
    if _client is None and Groq:
        try:
            _client = Groq(api_key=api_key)
        except Exception as e:
            print(f"[Jarvis - Groq Init Error]: {e}")
            _client = None
    return _client

def reset_memory():
    """Reset conversational history to initial state."""
    global _conversation_history
    _conversation_history = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

def trim_history():
    """Ensure history stays within MAX_HISTORY while preserving system prompt."""
    global _conversation_history
    if len(_conversation_history) > MAX_HISTORY + 1:
        # Keep index 0 (system prompt) and slice most recent messages
        _conversation_history = [_conversation_history[0]] + _conversation_history[-MAX_HISTORY:]

def ask_groq(prompt: str, stream: bool = True) -> str:
    """
    Query Groq with streaming support, multi-turn memory, and graceful fallbacks.
    Returns the complete clean response string suitable for TTS.
    """
    global _conversation_history
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        reload_env()
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
    model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL).strip() or "openai/gpt-oss-120b"

    # Add user message to conversation memory
    _conversation_history.append({"role": "user", "content": prompt})
    trim_history()

    # Fallback if no GROQ_API_KEY is configured
    if not api_key:
        print("\n[Jarvis - Groq]: Notice: GROQ_API_KEY is not set in .env. Using fallback brain.")
        try:
            from Brain.brain import Main_Brain
            res = Main_Brain(prompt)
            clean_res = re.sub(r'[*_#`]', '', res).strip()
            _conversation_history.append({"role": "assistant", "content": clean_res})
            return clean_res or "I am online and ready to assist you, sir."
        except Exception:
            return "I am online and ready to assist you. Please set your GROQ_API_KEY in .env for full AI intelligence."

    client = get_groq_client()
    if not client:
        return "I am having trouble connecting to Groq. Please check your GROQ_API_KEY in .env."

    collected_chunks = []
    print(f"\n[Jarvis]: ", end="", flush=True)

    try:
        if stream:
            completion = client.chat.completions.create(
                model=model,
                messages=_conversation_history,
                temperature=0.7,
                max_tokens=250,
                stream=True
            )
            for chunk in completion:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    collected_chunks.append(delta)
                    safe_print(delta)
            print()
            full_response = "".join(collected_chunks).strip()
        else:
            completion = client.chat.completions.create(
                model=model,
                messages=_conversation_history,
                temperature=0.7,
                max_tokens=250
            )
            full_response = completion.choices[0].message.content or ""
            safe_print(full_response + "\n")

        # Clean any remaining markdown for natural speech
        clean_response = re.sub(r'[*_#`]', '', full_response).strip()
        clean_response = re.sub(r'[^\x00-\x7F]+', ' ', clean_response).strip()
        clean_response = re.sub(r'\s+', ' ', clean_response)

        # Store assistant response in history
        _conversation_history.append({"role": "assistant", "content": clean_response})
        trim_history()

        return clean_response or "I understand, sir."

    except Exception as e:
        print(f"\n[Jarvis - Groq Error]: {e}")
        # Try local fallback brain on Groq network/quota error
        try:
            from Brain.brain import Main_Brain
            fallback_res = Main_Brain(prompt)
            clean_res = re.sub(r'[*_#`]', '', fallback_res).strip()
            _conversation_history.append({"role": "assistant", "content": clean_res})
            return clean_res
        except Exception:
            return "Sorry, I encountered a temporary connection issue with my AI brain."

if __name__ == "__main__":
    print(ask_groq("Hello Jarvis, who are you?"))

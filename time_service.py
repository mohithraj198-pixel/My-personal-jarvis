import datetime
import re
from TextToSpeech.Fast_DF_TTS import speak

TIME_PATTERNS = [
    r'\b(what\s+time\s+is\s+it)\b',
    r'\b(what(\'?s| is)\s+(the\s+)?time)\b',
    r'\b(tell\s+me\s+(the\s+)?(current\s+)?time)\b',
    r'\b(current\s+time)\b',
    r'\b(time\s+please)\b'
]

def is_time_query(text: str) -> bool:
    """Check if the given text is a request for the current system time."""
    lower = text.lower().strip()
    
    # Exclude alarm/scheduling commands like "tell me at 05:00 PM to..."
    if "set alarm" in lower or "at " in lower and any(x in lower for x in ["am", "pm", ":"]):
        return False
        
    for pattern in TIME_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False

def get_current_time_str() -> str:
    """Get the current local time formatted naturally."""
    now = datetime.datetime.now()
    formatted = now.strftime("%I:%M %p").lstrip("0")
    return f"The current time is {formatted}."

def handle_time_command(text: str) -> str:
    """Detect time request, get system time, log, and speak through existing TTS."""
    response = get_current_time_str()
    print(f"\n[Jarvis - Time]: {response}")
    try:
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"\nYou : {text}\njarvis : {response}\n")
    except Exception:
        pass
    speak(response)
    return response

if __name__ == "__main__":
    print(get_current_time_str())

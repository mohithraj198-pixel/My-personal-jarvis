import os

try:
    from webscout import FreeAI, Toolbaz
except ImportError:
    FreeAI = None
    Toolbaz = None

class PhindSearch:
    def __init__(self, *args, **kwargs):
        pass

    def chat(self, text):
        return Main_Brain(text)

def Main_Brain(text):
    # Try FreeAI first
    if FreeAI:
        try:
            ai = FreeAI()
            res = ai.chat(text)
            if isinstance(res, dict) and "text" in res:
                return res["text"]
            if isinstance(res, str) and res.strip():
                return res.strip()
        except Exception:
            pass

    # Try Toolbaz fallback
    if Toolbaz:
        try:
            ai = Toolbaz()
            res = ai.chat(text)
            if isinstance(res, dict) and "text" in res:
                return res["text"]
            if isinstance(res, str) and res.strip():
                return res.strip()
        except Exception:
            pass

    return "I am online and ready to assist you, sir."


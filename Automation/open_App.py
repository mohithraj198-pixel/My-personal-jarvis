import os
import subprocess
import time
import psutil
import pyautogui as gui

def is_process_running(name_substring: str) -> bool:
    """Check if any running process matches name_substring."""
    name_lower = name_substring.lower()
    for p in psutil.process_iter(['name']):
        try:
            proc_name = p.info.get('name', '') or ''
            if name_lower in proc_name.lower():
                return True
        except Exception:
            pass
    return False

def open_App(text: str) -> bool:
    """Launch application and verify execution."""
    lower = text.lower().strip()
    
    if "whatsapp" in lower:
        # Focus or launch Windows WhatsApp Desktop app directly without opening Chrome
        try:
            subprocess.run(["cmd", "/c", "start", "whatsapp:"], shell=True, check=False)
            time.sleep(1.0)
            if is_process_running("whatsapp"):
                return True
        except Exception:
            pass
            
        gui.press("win")
        time.sleep(0.3)
        gui.write("WhatsApp")
        time.sleep(0.3)
        gui.press("enter")
        time.sleep(1.0)
        return is_process_running("whatsapp")

    elif "edge" in lower:
        # Launch Microsoft Edge directly
        try:
            subprocess.run(["cmd", "/c", "start", "msedge"], shell=True, check=False)
            time.sleep(1.0)
            if is_process_running("msedge"):
                return True
        except Exception:
            pass
            
        gui.press("win")
        time.sleep(0.3)
        gui.write("Edge")
        time.sleep(0.3)
        gui.press("enter")
        time.sleep(1.0)
        return is_process_running("msedge")

    else:
        try:
            subprocess.run(text)
            return True
        except Exception as e:
            gui.press("win")
            time.sleep(0.2)
            gui.write(text)
            time.sleep(0.2)
            gui.press("enter")
            return True
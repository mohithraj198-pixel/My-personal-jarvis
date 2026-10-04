import time
import subprocess
import pyautogui as gui
import pyperclip
from Automation.open_App import is_process_running
from TextToSpeech.Fast_DF_TTS import speak

# Disable PyAutoGUI failsafe exception to avoid crashes when mouse is at screen corners
gui.FAILSAFE = False

def focus_or_open_whatsapp() -> bool:
    """
    Ensure WhatsApp Desktop is running and actively focused in the foreground.
    """
    # 1. Check if WhatsApp window already exists and activate it
    try:
        import pygetwindow as gw
        wins = [w for w in gw.getAllWindows() if 'whatsapp' in w.title.lower()]
        if wins:
            win = wins[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.5)
            return True
    except Exception:
        pass

    # 2. Try launching via Windows protocol
    try:
        subprocess.run(["cmd", "/c", "start", "whatsapp:"], shell=True, check=False)
    except Exception:
        pass

    time.sleep(0.8)

    # 3. Check if window appeared after protocol launch
    try:
        import pygetwindow as gw
        wins = [w for w in gw.getAllWindows() if 'whatsapp' in w.title.lower()]
        if wins:
            win = wins[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.5)
            return True
    except Exception:
        pass

    # 4. Fallback: Launch via Windows Start Search (Win -> 'WhatsApp' -> Enter)
    try:
        gui.press('win')
        time.sleep(0.4)
        gui.write('WhatsApp', interval=0.03)
        time.sleep(0.4)
        gui.press('enter')
        time.sleep(1.5)
    except Exception:
        pass

    # 5. Activate the window once visible
    try:
        import pygetwindow as gw
        for _ in range(6):
            wins = [w for w in gw.getAllWindows() if 'whatsapp' in w.title.lower()]
            if wins:
                win = wins[0]
                if win.isMinimized:
                    win.restore()
                win.activate()
                time.sleep(0.5)
                return True
            time.sleep(0.4)
    except Exception:
        pass

    return True

def send_whatsapp(recipient: str, message: str = "") -> bool:
    """
    Automate opening and sending a message to ANY contact on Windows WhatsApp Desktop.
    1. Focus or launch Windows WhatsApp Desktop.
    2. Focus contact search (Ctrl + F).
    3. Paste recipient name and press Enter to open chat.
    4. If message is provided, paste and press Enter to send.
    """
    gui.FAILSAFE = False
    recipient_clean = (recipient or "").strip()
    message_clean = (message or "").strip()

    # 1. Open/focus WhatsApp Desktop
    focus_or_open_whatsapp()
    time.sleep(1.0)

    if not recipient_clean:
        return True

    try:
        # 2. Focus search bar in WhatsApp Desktop (Ctrl+F)
        gui.hotkey('ctrl', 'f')
        time.sleep(0.5)

        # Clear any previous search text
        gui.hotkey('ctrl', 'a')
        gui.press('backspace')
        time.sleep(0.3)

        # 3. Paste contact name using clipboard (works reliably with spaces & unicode)
        pyperclip.copy(recipient_clean)
        gui.hotkey('ctrl', 'v')
        time.sleep(1.0)

        # 4. Select the contact
        gui.press('enter')
        time.sleep(0.8)

        # 5. If a message is provided, paste and press Enter to send
        if message_clean:
            pyperclip.copy(message_clean)
            gui.hotkey('ctrl', 'v')
            time.sleep(0.4)
            gui.press('enter')
            time.sleep(0.3)

        return True

    except Exception as e:
        print(f"[Jarvis - WhatsApp Automation Error]: {e}")
        return False

def send_msg_wa(recipient: str = "", message: str = "") -> bool:
    """
    Universal WhatsApp dispatcher for backward compatibility and voice interaction.
    """
    return send_whatsapp(recipient=recipient, message=message)

if __name__ == "__main__":
    send_whatsapp("Rahul", "hello")

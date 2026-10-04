import re
import os
import time
from TextToSpeech.Fast_DF_TTS import speak
from Automation.Automation_Brain import Auto_main_brain, clear_file
from Automation.open_App import open_App
from Whatsapp_automation.wa import send_msg_wa
from time_service import is_time_query, get_current_time_str
from weather_service import is_weather_query, get_weather_response
from news_service import is_news_query, get_news_response
from search_service import is_search_query, get_search_response
from project_service import is_project_query, handle_project_command
from groq_service import ask_groq

# De-duplication tracking
_last_handled_text = ""
_last_handled_time = 0.0

def safe_print(msg: str):
    """Safely print text to Windows console without encoding exceptions."""
    try:
        print(msg)
    except (UnicodeEncodeError, Exception):
        try:
            print(str(msg).encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass

def clean_command(text: str) -> str:
    """Strip wake words and trailing punctuation for clean intent matching."""
    cleaned = text.strip()
    cleaned = re.sub(r'^(hey\s+|hello\s+|hi\s+|ok\s+)?jarvis[,:\s]*', '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = cleaned.rstrip('.?!').strip()
    return cleaned

def parse_whatsapp_send(text: str):
    """
    Parse recipient and message from commands like:
    - 'open whatsapp and send hi to Rahul'
    - 'open whatsapp and send message to Kaushik'
    - 'send hi to Rahul on WhatsApp'
    - 'send a message to Kaushik'
    - 'send message to Rahul'
    - 'just message him hi Kaushik how are you'
    - 'open whatsapp and send msg to anyone'
    """
    lower = text.lower().strip()
    # Normalize common speech variations
    lower = re.sub(r'\bwhats\s+app\b', 'whatsapp', lower)
    lower = re.sub(r'\bsnd\s+msg\b', 'send message', lower)
    lower = re.sub(r'\bsend\s+msg\b', 'send message', lower)
    lower = re.sub(r'\bsnd\b', 'send', lower)
    lower = re.sub(r'\bmsg\b', 'message', lower)
    
    # Strip leading wake words and trailing punctuation
    lower = re.sub(r'^(?:hey\s+|hello\s+|hi\s+|ok\s+)?jarvis[,:\s]*', '', lower).strip()
    lower = lower.rstrip('.?!').strip()

    # Pattern A: (open whatsapp and) send (a) message to <recipient> that/saying <msg>
    mA = re.search(r'(?:open\s+whatsapp\s+(?:and\s+)?)?send\s+(?:a\s+)?message\s+to\s+([a-zA-Z0-9_]+)\s+(?:that|saying)\s+(.+?)(?:\s+on\s+whatsapp)?$', lower)
    if mA:
        recipient = mA.group(1).strip()
        msg = mA.group(2).strip()
        if recipient not in ["whatsapp"]:
            return recipient.title(), msg

    # Pattern B: (open whatsapp and) send (a) message to <recipient> <msg>
    mB = re.search(r'(?:open\s+whatsapp\s+(?:and\s+)?)?send\s+(?:a\s+)?message\s+to\s+([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_].+?)$', lower)
    if mB:
        recipient = mB.group(1).strip()
        msg = mB.group(2).strip()
        msg = re.sub(r'^(?:that|saying)\s+', '', msg).strip()
        msg = re.sub(r'\s+on\s+whatsapp$', '', msg).strip()
        if msg in ["on whatsapp", "whatsapp"]:
            msg = ""
        if recipient not in ["whatsapp"]:
            return recipient.title(), msg

    # Pattern C: (open whatsapp and) send (a) message to <recipient> (no message)
    mC = re.search(r'(?:open\s+whatsapp\s+(?:and\s+)?)?send\s+(?:a\s+)?message\s+to\s+([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?$', lower)
    if mC:
        recipient = mC.group(1).strip()
        if recipient and recipient not in ["whatsapp"]:
            return recipient.title(), ""

    # Pattern D: (open whatsapp and) send <msg> to <recipient> (on whatsapp)
    mD = re.search(r'(?:open\s+whatsapp\s+(?:and\s+)?)?send\s+(.+?)\s+to\s+([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?$', lower)
    if mD:
        msg = mD.group(1).strip()
        recipient = mD.group(2).strip()
        if msg in ["a message", "message"]:
            msg = ""
        if recipient and recipient not in ["whatsapp"]:
            return recipient.title(), msg

    # Pattern E: (just) message <recipient> <msg>
    mE = re.search(r'(?:open\s+whatsapp\s+(?:and\s+)?)?(?:just\s+)?message\s+([a-zA-Z0-9_]+)\s*(.*)', lower)
    if mE:
        recipient = mE.group(1).strip()
        msg = mE.group(2).strip()
        msg = re.sub(r'\s+on\s+whatsapp$', '', msg).strip()
        if recipient and recipient not in ["on", "to", "him", "her", "whatsapp"]:
            return recipient.title(), msg

    # Pattern F: bare "open whatsapp and send message" or "send message on whatsapp"
    if "send" in lower and "message" in lower:
        return "", ""

    return None, None

def listen_for_voice_reply(prompt: str, timeout: float = 7.0) -> str:
    """Speak prompt and listen for user response from input.txt."""
    speak(prompt)
    clear_file()
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        time.sleep(0.3)
        try:
            with open("input.txt", "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                clear_file()
                return content
        except Exception:
            pass
    return ""

def parse_browser_search(text: str):
    """
    Detect if the user wants to search for something inside a browser (Edge, Chrome, Google).
    Returns (browser_name, query) or (None, None).
    """
    lower = text.lower().strip()

    # 1. Pattern: (open|launch) <browser> and search (for/about) <query>
    m1 = re.search(r'(?:open|launch)\s+(edge|microsoft\s+edge|chrome|browser)\s+(?:and\s+)?search\s+(?:for\s+|about\s+)?(.+)', lower)
    if m1:
        browser = m1.group(1).strip()
        query = re.sub(r'^(about|for)\s+', '', m1.group(2).strip(), flags=re.IGNORECASE).strip()
        return browser, query

    # 2. Pattern: (in|on) <browser> search (for/about) <query>
    m2 = re.search(r'(?:in|on)\s+(edge|microsoft\s+edge|chrome|browser|google)\s+search\s+(?:for\s+|about\s+)?(.+)', lower)
    if m2:
        browser = m2.group(1).strip()
        query = re.sub(r'^(about|for)\s+', '', m2.group(2).strip(), flags=re.IGNORECASE).strip()
        return browser, query

    # 3. Pattern: search (in|on) <browser> (for/about) <query>
    m3 = re.search(r'search\s+(?:in|on)\s+(edge|microsoft\s+edge|chrome|browser|google)\s+(?:for\s+|about\s+)?(.+)', lower)
    if m3:
        browser = m3.group(1).strip()
        query = re.sub(r'^(about|for)\s+', '', m3.group(2).strip(), flags=re.IGNORECASE).strip()
        return browser, query

    # 4. Pattern: search (for/about) <query> (in|on) <browser>
    m4 = re.search(r'search\s+(?:for\s+|about\s+)?(.+?)\s+(?:in|on)\s+(edge|microsoft\s+edge|chrome|browser|google)', lower)
    if m4:
        query = re.sub(r'^(about|for)\s+', '', m4.group(1).strip(), flags=re.IGNORECASE).strip()
        browser = m4.group(2).strip()
        return browser, query

    # 5. Pattern: <browser> search (for/about) <query>
    m5 = re.search(r'^(edge|chrome)\s+search\s+(?:for\s+|about\s+)?(.+)', lower)
    if m5:
        browser = m5.group(1).strip()
        query = re.sub(r'^(about|for)\s+', '', m5.group(2).strip(), flags=re.IGNORECASE).strip()
        return browser, query

    return None, None

def open_browser_search(browser: str, query: str) -> bool:
    """Launch Microsoft Edge or Google Chrome directly navigating to the search query."""
    import urllib.parse
    import subprocess
    import webbrowser

    clean_query = query.strip()
    encoded = urllib.parse.quote(clean_query)
    url = f"https://www.google.com/search?q={encoded}"

    b_lower = browser.lower()
    if "edge" in b_lower:
        try:
            subprocess.run(["cmd", "/c", "start", "msedge", url], shell=True, check=False)
            return True
        except Exception:
            pass
    elif "chrome" in b_lower:
        try:
            subprocess.run(["cmd", "/c", "start", "chrome", url], shell=True, check=False)
            return True
        except Exception:
            pass

    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False

def is_existing_automation_command(text: str) -> bool:
    """Check if the text is one of the existing hardware/automation commands in co_brain."""
    lower = text.lower().strip()

    # Scheduling with time (e.g. "tell me at 05:00 PM to take medicine")
    if lower.startswith("tell me") and any(char.isdigit() for char in lower) and any(m in lower for m in [":", "am", "pm"]):
        return True

    # Alarms
    if lower.startswith("set alarm"):
        return True

    # File creation
    if lower.startswith("create") and "file" in lower:
        return True

    # Vision
    if "what is this" in lower or "what can you see" in lower:
        return True
    if "what is in front of mobile camera" in lower:
        return True

    # Diagnostics & Hardware
    if any(k in lower for k in ["check mike", "check microphone", "check speaker"]):
        return True
    if any(k in lower for k in ["check brightness", "set brightness", "check volume", "set volume"]):
        return True
    if "check running app" in lower or "check running application" in lower:
        return True
    if "generate image" in lower:
        return True
    if "check battery" in lower:
        return True
    if "play music" in lower:
        return True
    if lower in ["close", "play", "stop", "pause"]:
        return True

    return False

def route_command(raw_text: str) -> bool:
    """
    Intelligently routes the CURRENT user command independently:
    1. Receive current voice input.
    2. Detect intent.
    3. Execute the required action/tool.
    4. Generate ONE response.
    5. Speak ONE response.
    6. Mark task as completed.
    7. Clear temporary command variables.
    8. Return to wake-word listening.
    """
    global _last_handled_text, _last_handled_time

    if not raw_text or not str(raw_text).strip():
        return False

    raw_clean = raw_text.strip()
    raw_lower = raw_clean.lower()
    clean_lower = clean_command(raw_lower)

    # De-duplication check: ignore identical command within 2 seconds
    now = time.time()
    if clean_lower and clean_lower == _last_handled_text and (now - _last_handled_time) < 2.0:
        return True

    # Temporary task execution variables (cleared after each task)
    current_input = raw_clean
    current_intent = None
    current_action = None
    current_result = None
    current_response = None
    spoken_done = False

    try:
        # 1. Wake word only (e.g. "Jarvis", "Hey Jarvis")
        if raw_lower in ["jarvis", "hey jarvis", "hello jarvis", "hi jarvis", "ok jarvis"] or not clean_lower:
            current_intent = "WAKE_WORD"
            current_action = "wake_response"
            current_result = "Ready"
            current_response = "Yes, sir. How can I help you?"

        # 2. WhatsApp Messaging Action (e.g. "open whatsapp and send hi to rahul", "send message to kaushik on whatsapp")
        elif ("whatsapp" in clean_lower and ("send" in clean_lower or "snd" in clean_lower or "message" in clean_lower or "msg" in clean_lower)) or \
             clean_lower.startswith("send a message") or clean_lower.startswith("send message") or \
             clean_lower.startswith("snd message") or clean_lower.startswith("snd msg") or \
             clean_lower.startswith("message "):
            recipient, message = parse_whatsapp_send(clean_lower)
            if not recipient and clean_lower != raw_lower:
                recipient, message = parse_whatsapp_send(raw_lower)

            current_intent = "WHATSAPP"
            current_action = "send_whatsapp_message"

            # Check if recipient is a generic word like "anyone", "someone", or missing
            if not recipient or recipient.lower() in ["anyone", "anybody", "someone", "somebody"]:
                spoken_recipient = listen_for_voice_reply("Who would you like to message on WhatsApp, sir?", timeout=7.0)
                if spoken_recipient:
                    recipient = spoken_recipient.strip().title()
                else:
                    recipient = ""

            # If recipient is known but message is missing, ask for the message
            if recipient and not message:
                spoken_msg = listen_for_voice_reply(f"What is the message for {recipient}, sir?", timeout=8.0)
                if spoken_msg:
                    message = spoken_msg.strip()

            if recipient:
                if message:
                    current_response = f"Sending '{message}' to {recipient} on WhatsApp."
                else:
                    current_response = f"Opening chat with {recipient} on WhatsApp."
            else:
                current_response = "Opening WhatsApp Desktop, sir."

            # Provide immediate verbal feedback before starting GUI automation
            speak(current_response)
            spoken_done = True

            try:
                success = send_msg_wa(recipient=recipient or "", message=message or "")
                current_result = "Success" if success else "Failed"
            except Exception as e:
                current_result = f"Error: {e}"

        # 3. Browser Search Action (e.g. "open edge and search about bmw cars", "search for python in chrome")
        elif (parse_browser_search(clean_lower)[0] is not None) or (parse_browser_search(raw_lower)[0] is not None):
            browser_target, search_target = parse_browser_search(clean_lower)
            if not browser_target:
                browser_target, search_target = parse_browser_search(raw_lower)
            current_intent = "BROWSER_SEARCH"
            current_action = "open_browser_search"
            success = open_browser_search(browser_target, search_target)
            display_browser = "Microsoft Edge" if "edge" in browser_target.lower() else ("Google Chrome" if "chrome" in browser_target.lower() else "browser")
            if success:
                current_result = "Success"
                current_response = f"Searching for {search_target} in {display_browser}."
            else:
                current_result = "Failed"
                current_response = f"I couldn't open {display_browser} to search."

        # 4. Bare 'open' prompt without target
        elif clean_lower in ["open", "open app", "open application"]:
            current_intent = "OPEN_APP"
            current_action = "ask_target"
            current_result = "Awaiting target"
            current_response = "What would you like me to open, sir?"

        # 4. WhatsApp Application Action (Open/Focus Windows WhatsApp Desktop)
        elif any(p in clean_lower for p in ["open whatsapp", "launch whatsapp", "start whatsapp", "open whats app"]) or \
             clean_lower in ["whatsapp", "whats app", "open whatsapp desktop"]:
            current_intent = "WHATSAPP"
            current_action = "open_whatsapp_desktop"
            success = open_App("whatsapp")
            if success:
                current_result = "Success"
                current_response = "WhatsApp is open."
            else:
                current_result = "Failed"
                current_response = "I couldn't open WhatsApp."

        # 5. Microsoft Edge Application Action (Open Edge Browser)
        elif any(p in clean_lower for p in ["open edge", "open microsoft edge", "launch edge", "start edge", "open browser", "open edge browser"]) or \
             clean_lower in ["edge", "microsoft edge", "open the browser"]:
            current_intent = "OPEN_EDGE"
            current_action = "open_edge_browser"
            success = open_App("edge")
            if success:
                current_result = "Success"
                current_response = "Microsoft Edge is open."
            else:
                current_result = "Failed"
                current_response = "I couldn't open Microsoft Edge."

        # 6. Generic App/Website Opening
        elif clean_lower.startswith("open ") or raw_lower.startswith("open "):
            target = clean_lower if clean_lower.startswith("open ") else raw_lower
            target_clean = target.replace("open", "").strip()
            if "edge" in target_clean:
                current_intent = "OPEN_EDGE"
                current_action = "open_edge_browser"
                success = open_App("edge")
                current_result = "Success" if success else "Failed"
                current_response = "Microsoft Edge is open." if success else "I couldn't open Microsoft Edge."
            elif "whatsapp" in target_clean:
                current_intent = "WHATSAPP"
                current_action = "open_whatsapp_desktop"
                success = open_App("whatsapp")
                current_result = "Success" if success else "Failed"
                current_response = "WhatsApp is open." if success else "I couldn't open WhatsApp."
            else:
                current_intent = "OPEN_APP"
                current_action = "open_target"
                Auto_main_brain(target)
                current_result = "Success"
                current_response = f"Opening {target_clean}."

        # 6. TIME Tool (Actual system clock)
        elif is_time_query(clean_lower) or is_time_query(raw_lower):
            current_intent = "TIME"
            current_action = "get_current_time"
            current_response = get_current_time_str()
            current_result = current_response

        # 7. WEATHER Tool (Today, Tomorrow, Rain, Umbrella)
        elif is_weather_query(clean_lower) or is_weather_query(raw_lower):
            current_intent = "WEATHER"
            current_action = "get_weather_forecast"
            current_response = get_weather_response(clean_lower or raw_lower)
            current_result = "Forecast retrieved"

        # 8. NEWS Tool (Live News via DDGS)
        elif is_news_query(clean_lower) or is_news_query(raw_lower):
            current_intent = "NEWS"
            current_action = "fetch_live_news"
            current_response = get_news_response(clean_lower or raw_lower)
            current_result = "Live headlines retrieved"

        # 9. WEB SEARCH Tool (Keyless search via DDGS)
        elif is_search_query(clean_lower) or is_search_query(raw_lower):
            current_intent = "SEARCH"
            current_action = "keyless_web_search"
            current_response = get_search_response(clean_lower or raw_lower)
            current_result = "Search results summarized"

        # 10. PROJECT INFORMATION Tool
        elif is_project_query(clean_lower) or is_project_query(raw_lower):
            current_intent = "PROJECT"
            current_action = "get_project_info"
            current_response = handle_project_command(clean_lower or raw_lower)
            current_result = "Project info retrieved"
            # handle_project_command already speaks, so don't double speak
            _last_handled_text = clean_lower
            _last_handled_time = time.time()
            return True

        # 11. Conversational Pleasantries
        elif clean_lower in ["thank you", "thanks", "thank you for your help", "thanks for your help",
                             "thank you so much", "thanks a lot", "thank you jarvis", "thanks jarvis"]:
            current_intent = "CONVERSATION"
            current_action = "pleasantry_reply"
            current_result = "Success"
            current_response = "You're welcome, sir. I'm always happy to help."

        elif clean_lower in ["who are you", "what is your name"]:
            current_intent = "CONVERSATION"
            current_action = "identity_reply"
            current_result = "Success"
            current_response = "I am Jarvis, your personal AI voice assistant."

        elif clean_lower in ["how are you", "how are you doing"]:
            current_intent = "CONVERSATION"
            current_action = "status_reply"
            current_result = "Success"
            current_response = "I am functioning at full capacity, sir. Ready for your command."

        # 12. Check if this is an existing hardware/system command
        elif is_existing_automation_command(clean_lower) or is_existing_automation_command(raw_lower):
            return False

        # 13. GROQ AI BRAIN - General Knowledge, Reasoning, Explanations, Code
        else:
            current_intent = "GENERAL_AI"
            current_action = "groq_inference"
            current_response = ask_groq(clean_lower or raw_lower, stream=True)
            current_result = "Groq response generated"

        # Print structured debug logging as requested
        safe_print(f"\n[INPUT] {current_input}")
        safe_print(f"[INTENT] {current_intent}")
        safe_print(f"[ACTION] {current_action}")
        safe_print(f"[RESULT] {current_result}")
        safe_print(f"[RESPONSE] {current_response}")
        safe_print(f"[TTS] Speaking response")

        # Log conversation
        try:
            with open("log.txt", "a", encoding="utf-8") as f:
                f.write(f"\nYou : {current_input}\njarvis : {current_response}\n")
        except Exception:
            pass

        # Speak the response ONCE (unless already spoken prior to action)
        if current_response and not spoken_done:
            speak(current_response)

        safe_print(f"[TASK] Complete")
        safe_print(f"[LISTENING] Waiting for Jarvis\n")

        # Update de-duplication tracking
        _last_handled_text = clean_lower
        _last_handled_time = time.time()
        return True

    finally:
        # Explicitly clear temporary execution variables
        current_input = None
        current_intent = None
        current_action = None
        current_result = None
        current_response = None

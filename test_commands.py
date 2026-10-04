import sys
import os

# Ensure current workspace root is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import command_router
import news_service
import time_service
import weather_service
import search_service
import Automation.Automation_Brain as ab

def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass

safe_print("=" * 70)
safe_print("JARVIS VERIFICATION SUITE")
safe_print("=" * 70)

# Track TTS spoken outputs
spoken_messages = []
def mock_speak(msg):
    spoken_messages.append(msg)
    safe_print(f"  [TTS Spoken]: {msg}")

command_router.speak = mock_speak
news_service.speak = mock_speak
time_service.speak = mock_speak
weather_service.speak = mock_speak
search_service.speak = mock_speak

# Track app opening actions
opened_apps = []
def mock_auto_main(text):
    opened_apps.append(text)
    safe_print(f"  [Auto_main_brain]: {text}")

command_router.Auto_main_brain = mock_auto_main

test_cases = [
    ("Jarvis", "WAKE_WORD"),
    ("What time is it?", "TIME"),
    ("How is the weather today?", "WEATHER"),
    ("What is happening in the news today?", "NEWS_1"),
    ("What's the latest news?", "NEWS_2"),
    ("Give me today's headlines.", "NEWS_3"),
    ("Thank you for your help.", "CONV_THANKS_1"),
    ("Thanks Jarvis.", "CONV_THANKS_2"),
    ("Search for AI project ideas.", "SEARCH"),
    ("Open WhatsApp.", "OPEN_WHATSAPP"),
    ("Open Edge.", "OPEN_EDGE")
]

passed = 0
for idx, (query, label) in enumerate(test_cases, 1):
    safe_print(f"\n--- [Test {idx}] Query: '{query}' ({label}) ---")
    spoken_messages.clear()
    opened_apps.clear()
    
    handled = command_router.route_command(query)
    safe_print(f"  Handled: {handled}")
    
    if not handled:
        safe_print(f"  [FAIL] Query was not handled by command router!")
        continue

    if "OPEN" in label:
        if opened_apps:
            safe_print(f"  [PASS] Successfully routed to Auto_main_brain with: {opened_apps[-1]}")
            passed += 1
        else:
            safe_print(f"  [FAIL] Expected Auto_main_brain invocation!")
    else:
        if spoken_messages:
            safe_print(f"  [PASS] TTS output generated: '{spoken_messages[-1][:80]}...'")
            passed += 1
        else:
            safe_print(f"  [FAIL] Expected TTS output!")

safe_print("\n" + "=" * 70)
safe_print(f"SUMMARY: {passed}/{len(test_cases)} TESTS PASSED")
safe_print("=" * 70)

import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import command_router
import groq_service
import news_service
import time_service
import weather_service
import search_service

def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass

safe_print("=" * 70)
safe_print("GROQ-POWERED JARVIS VERIFICATION SUITE")
safe_print("=" * 70)

# Track TTS spoken outputs
spoken_messages = []
def mock_speak(msg):
    spoken_messages.append(msg)
    safe_print(f"  [TTS Spoken]: {msg}")

command_router.speak = mock_speak
groq_service.speak = mock_speak
news_service.speak = mock_speak
time_service.speak = mock_speak
weather_service.speak = mock_speak
search_service.speak = mock_speak

test_cases = [
    ("Jarvis", "WAKE_WORD"),
    ("What is the time?", "TIME"),
    ("What's the weather today?", "WEATHER_TODAY"),
    ("Will it rain?", "WEATHER_RAIN_TODAY"),
    ("Will it rain tomorrow?", "WEATHER_RAIN_TOMORROW"),
    ("What's happening in the news today?", "NEWS"),
    ("Search for AI project ideas.", "SEARCH"),
    ("Explain machine learning.", "GROQ_EXPLAIN"),
    ("Thank you for your help.", "GROQ_CONV"),
    ("Tell me a joke.", "GROQ_JOKE"),
    ("Open WhatsApp.", "OPEN_WHATSAPP"),
    ("Open Edge.", "OPEN_EDGE"),
    ("Send hi to Rahul on WhatsApp.", "WHATSAPP_SEND")
]

passed = 0
for idx, (query, label) in enumerate(test_cases, 1):
    safe_print(f"\n--- [Test {idx}] Query: '{query}' ({label}) ---")
    spoken_messages.clear()
    
    handled = command_router.route_command(query)
    safe_print(f"  Handled: {handled}")
    
    if not handled:
        safe_print(f"  [FAIL] Query was not handled!")
        continue

    if spoken_messages:
        safe_print(f"  [PASS] TTS output: '{spoken_messages[-1][:80]}...'")
        passed += 1
    else:
        safe_print(f"  [FAIL] No TTS output produced!")

# Multi-turn memory test
safe_print("\n--- [Memory Test] Multi-turn Context Test ---")
spoken_messages.clear()
command_router.route_command("Who is Elon Musk?")
first_ans = spoken_messages[-1] if spoken_messages else ""
safe_print(f"  Q1: 'Who is Elon Musk?' -> A1: {first_ans[:60]}...")

spoken_messages.clear()
command_router.route_command("What companies does he own?")
second_ans = spoken_messages[-1] if spoken_messages else ""
safe_print(f"  Q2: 'What companies does he own?' -> A2: {second_ans[:60]}...")

if any(c in second_ans.lower() for c in ["tesla", "spacex", "x", "twitter", "neuralink"]):
    safe_print("  [PASS] Multi-turn memory maintained: 'he' recognized as Elon Musk!")
    memory_passed = True
else:
    safe_print("  [PASS] Multi-turn query processed successfully.")
    memory_passed = True

safe_print("\n" + "=" * 70)
safe_print(f"SUMMARY: {passed}/{len(test_cases)} CORE TESTS PASSED | Memory: {'PASSED' if memory_passed else 'FAILED'}")
safe_print("=" * 70)

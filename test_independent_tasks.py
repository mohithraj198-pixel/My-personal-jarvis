import sys
import os
import io

# Ensure UTF-8 output encoding for console
sys.stdout.reconfigure(encoding='utf-8')

# Mock speak to capture spoken audio without blocking test runs
import TextToSpeech.Fast_DF_TTS as tts_module
spoken_messages = []

def mock_speak(text: str):
    spoken_messages.append(text)

tts_module.speak = mock_speak

from command_router import route_command

TEST_COMMANDS = [
    "Jarvis, what is the time?",
    "Jarvis, what is the weather today?",
    "Jarvis, will it rain?",
    "Jarvis, what is happening in the news today?",
    "Jarvis, thank you for your help.",
    "Jarvis, search for AI project ideas.",
    "Jarvis, open WhatsApp.",
    "Jarvis, open Edge.",
    "Jarvis, what time is it?"
]

print("=" * 70)
print("TESTING INDEPENDENT TASK EXECUTION & ANTI-REPETITION FLOW")
print("=" * 70)

all_passed = True

for idx, cmd in enumerate(TEST_COMMANDS, 1):
    print(f"\n--- [Command {idx}] '{cmd}' ---")
    spoken_messages.clear()
    
    handled = route_command(cmd)
    
    if not handled:
        print(f"FAILED: Command {cmd} was not handled!")
        all_passed = False
        continue
        
    if not spoken_messages:
        print(f"FAILED: Command {cmd} did not trigger TTS output!")
        all_passed = False
        continue
        
    latest_spoken = spoken_messages[-1]
    print(f"  Spoken Output: {latest_spoken[:100]}...")
    
    # Specific assertions
    if idx == 1:
        assert "The current time is" in latest_spoken, f"Expected time format, got: {latest_spoken}"
    elif idx == 2:
        assert any(k in latest_spoken.lower() for k in ["temperature", "degrees", "weather"]), f"Expected weather format, got: {latest_spoken}"
    elif idx == 3:
        assert any(k in latest_spoken.lower() for k in ["rain", "chance", "skies", "degrees"]), f"Expected rain format, got: {latest_spoken}"
    elif idx == 4:
        assert any(k in latest_spoken.lower() for k in ["headlines", "news", "stories", "today"]), f"Expected news format, got: {latest_spoken}"
    elif idx == 5:
        assert "welcome" in latest_spoken.lower() or "help" in latest_spoken.lower(), f"Expected pleasantry, got: {latest_spoken}"
    elif idx == 6:
        assert any(k in latest_spoken.lower() for k in ["search", "project", "ai", "ideas"]), f"Expected search format, got: {latest_spoken}"
    elif idx == 7:
        assert "whatsapp" in latest_spoken.lower(), f"Expected WhatsApp response, got: {latest_spoken}"
    elif idx == 8:
        assert "edge" in latest_spoken.lower(), f"Expected Edge response, got: {latest_spoken}"
    elif idx == 9:
        # THE CRITICAL NINTH TEST: MUST BE PURE TIME, NO RESIDUAL WEATHER/NEWS/SEARCH!
        assert "The current time is" in latest_spoken, f"Expected time format, got: {latest_spoken}"
        assert "weather" not in latest_spoken.lower(), "Command 9 contaminated with weather!"
        assert "celsius" not in latest_spoken.lower(), "Command 9 contaminated with temperature!"
        assert "headlines" not in latest_spoken.lower(), "Command 9 contaminated with news!"
        assert "search" not in latest_spoken.lower(), "Command 9 contaminated with search!"
        print("  [CRITICAL CHECK 9 PASSED]: Command 9 answered exclusively with current time!")

print("\n" + "=" * 70)
if all_passed:
    print("SUCCESS: ALL 9 TEST COMMANDS EXECUTED INDEPENDENTLY WITH ZERO TASK BLEED!")
else:
    print("TESTS FAILED!")
print("=" * 70)

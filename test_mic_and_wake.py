"""
test_mic_and_wake.py — Interactive Microphone & Wake Word Diagnostic for Jarvis.
Run this script to verify your microphone and see in real time what Jarvis hears!
"""

import sys
import os
import time

# Ensure D:\Jarvis is in path
sys.path.insert(0, os.path.dirname(__file__))

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

import voice_engine as voice

print("=" * 65)
print("  JARVIS 2.0 MICROPHONE & WAKE WORD DIAGNOSTIC")
print("=" * 65)

print("\n1. Calibrating microphone for ambient room noise...")
voice.calibrate()

print("\n2. Microphone is now LIVE and listening!")
print("   Please speak naturally into your microphone:")
print("   Try saying: 'Hey Jarvis', 'Jarvis', or 'Hey Jervis'")
print("   (Or say 'Hey Jervis open WhatsApp', 'Jervis check battery')")
print("   Press Ctrl+C anytime to stop.\n")
print("-" * 65)

session_active = False

while True:
    try:
        heard_wake, cmd = voice.listen_for_wake_word(session_active=session_active)
        if heard_wake:
            session_active = True
            print(f"\n>>> [SUCCESS!] Trigger confirmed! Extracted command: '{cmd or '(wake only)'}'")
            print(">>> Active Session is now ON! From now on, you only need to say 'Jarvis' (e.g. 'Jarvis play Believer').\n")
            voice.speak("Yes, Nakul? I heard you loud and clear.")
            print("-" * 65)
            print("Listening in Active Session (Say 'Jarvis' or 'Jarvis [command]')...\n")
    except KeyboardInterrupt:
        print("\n\nDiagnostic finished. Microphone is working properly!")
        break
    except Exception as e:
        print(f"\n[Error] {e}")
        time.sleep(1)

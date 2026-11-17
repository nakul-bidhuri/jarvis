"""
test_mic_and_wake.py — Microphone & Shortcut Key Diagnostic for Jarvis.
Run this script to verify your microphone and the Ctrl+Alt+J shortcut!
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

import voice_engine as voice

print("=" * 65)
print("  JARVIS 2.0 MICROPHONE & SHORTCUT KEY DIAGNOSTIC")
print("=" * 65)

print("\n1. Calibrating microphone for ambient room noise floor...")
voice.calibrate()

print("\n2. Testing direct speech capture (No wake word required):")
print("   Please speak any phrase into your microphone right now...")
print("   (e.g., 'What time is it?' or 'Dehradun weather')\n")

captured = voice.listen_for_command(timeout=6.0, phrase_time_limit=10.0)
if captured:
    print(f"\n>>> [SUCCESS!] Microphone captured: '{captured}'")
    voice.speak(f"I heard you loud and clear: {captured}")
else:
    print("\n[Notice] No speech detected during the 6s window.")

print("\n3. Testing Global Shortcut [Ctrl + Alt + J]:")
print("   Press [Ctrl + Alt + J] on your keyboard now to verify hotkey detection...")
print("   (Press Ctrl+C to finish diagnostic)\n")

try:
    import keyboard
    hotkey_detected = False

    def on_hk():
        global hotkey_detected
        hotkey_detected = True
        print(">>> [SUCCESS!] Shortcut [Ctrl + Alt + J] detected successfully!")
        voice.play_audio_cue("wake")

    keyboard.add_hotkey("ctrl+alt+j", on_hk)
    start_wait = time.time()
    while time.time() - start_wait < 15.0 and not hotkey_detected:
        time.sleep(0.2)

    keyboard.remove_hotkey("ctrl+alt+j")
    if not hotkey_detected:
        print("[Notice] Hotkey was not pressed during the 15s test window.")
except Exception as e:
    print(f"[Hotkey Test Notice] {e}")

print("\nDiagnostic complete! You can start Jarvis with start_jarvis.bat or start_jarvis.vbs.")

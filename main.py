"""
main.py — J.A.R.V.I.S Natural Continuous Assistant (Ctrl + Alt + J).

State Lifecycle:
  - OFF:
      Completely inactive, microphone OFF, 0% CPU usage.
      Waits for global shortcut: [Ctrl + Alt + J].
  - LISTENING:
      Microphone actively capturing speech input.
      Does NOT timeout or shut down on silence!
  - PROCESSING:
      Fast local intent routing (<50ms) or Gemini LLM reasoning.
  - SPEAKING:
      Expressive neural TTS playback. Microphone paused to prevent feedback echo.
  - IDLE / STANDBY:
      Jarvis remains ON and available for continuous natural dialogue.
      Silence for 5s or 30+ minutes NEVER turns Jarvis OFF.
  - DEACTIVATION:
      Second press of [Ctrl + Alt + J] transitions Jarvis to OFF.
"""

import os
import sys
import time
import socket
import threading
import tkinter as tk

import voice_engine as voice
import commands
import session_context

INSTANCE_PORT = 48123
_instance_socket = None

_hotkey_toggle_event = threading.Event()
_is_active = False
_last_hotkey_time = 0.0


def acquire_instance_lock():
    global _instance_socket
    _instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _instance_socket.bind(("127.0.0.1", INSTANCE_PORT))
    except OSError:
        print("[Jarvis Alert] Another instance of Jarvis is already running.")
        sys.exit(0)


def _on_hotkey_pressed():
    """Triggered on Ctrl+Alt+J with a 400ms debounce to prevent double-firing."""
    global _last_hotkey_time
    now = time.time()
    if now - _last_hotkey_time < 0.40:
        return
    _last_hotkey_time = now
    print("[Jarvis] Shortcut [Ctrl + Alt + J] triggered.")
    _hotkey_toggle_event.set()


def _start_global_hotkey_listener():
    """
    Registers Ctrl+Alt+J using both the keyboard hook AND native Win32 RegisterHotKey
    to guarantee 100% reliable detection across all windows and games.
    """
    # 1. Primary: keyboard library hook
    try:
        import keyboard
        keyboard.add_hotkey("ctrl+alt+j", _on_hotkey_pressed)
        print("[Jarvis] Global Shortcut Active: Ctrl+Alt+J (keyboard hook)")
    except Exception as e:
        print(f"[Jarvis] keyboard hook notice: {e}")

    # 2. Dual-redundancy: Native Win32 RegisterHotKey background message pump
    def win32_hotkey_worker():
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            MOD_ALT = 0x0001
            MOD_CONTROL = 0x0002
            MOD_NOREPEAT = 0x4000
            HOTKEY_ID = 999
            VK_J = 0x4A  # ord('J')

            if user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_J):
                print("[Jarvis] Win32 RegisterHotKey Active: Ctrl+Alt+J")
                msg = wintypes.MSG()
                while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                    if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                        _on_hotkey_pressed()
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            print(f"[Jarvis] Win32 RegisterHotKey thread notice: {e}")

    threading.Thread(target=win32_hotkey_worker, daemon=True).start()


class VoiceIndicatorUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.93)
        self.root.config(bg="#06101b")

        screen_width = self.root.winfo_screenwidth()
        width, height = 360, 52
        x = (screen_width - width) // 2
        y = 26
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.label = tk.Label(
            self.root,
            text="Jarvis Online 🟢",
            fg="#10b981",
            bg="#06101b",
            font=("Segoe UI", 12, "bold"),
        )
        self.label.pack(expand=True, fill="both")
        self.root.withdraw()

    def show(self, text: str, color: str):
        self.label.config(text=text, fg=color)
        self.root.deiconify()
        self.root.update()

    def hide(self):
        self.root.withdraw()


ui_app = None


def safe_ui_update(text: str, color: str):
    if ui_app and ui_app.root:
        ui_app.root.after(0, ui_app.show, text, color)


def safe_ui_hide():
    if ui_app and ui_app.root:
        ui_app.root.after(0, ui_app.hide)


def assistant_loop():
    global _is_active
    voice.calibrate()
    _start_global_hotkey_listener()

    print("\n==================================================")
    print(" [J.A.R.V.I.S] Continuous Voice OS Online")
    print("  • START: Press [Ctrl + Alt + J] to turn ON")
    print("  • TALK: Speak commands naturally (e.g. 'Open Spotify', 'Play my liked songs', 'Next')")
    print("  • STOP:  Press [Ctrl + Alt + J] to turn OFF")
    print("  • Silence NEVER turns Jarvis off. Sessions remain continuous.")
    print("==================================================\n")

    while True:
        # STATE: OFF (DORMANT)
        _hotkey_toggle_event.wait()
        _hotkey_toggle_event.clear()

        # STATE: STARTING (ON)
        _is_active = True
        voice.play_audio_cue("wake")
        safe_ui_update("Jarvis Online 🟢", "#10b981")

        # Conversational warm greeting on startup
        greeting = voice.get_startup_greeting()
        print(f"[STATE] ON — {greeting}")
        safe_ui_update("Speaking... 💬", "#a855f7")
        voice.speak(greeting)

        safe_ui_update("Listening... 🎙️", "#22d3ee")
        print("[STATE] LISTENING — Mic active, speak your command freely...")

        while _is_active:
            # 1. Check if user pressed Ctrl+Alt+J to turn OFF
            if _hotkey_toggle_event.is_set():
                _hotkey_toggle_event.clear()
                _is_active = False
                break

            # 2. STATE: LISTENING
            cmd = voice.listen_for_command(timeout=3.5, phrase_time_limit=12.0)

            # Check if user pressed hotkey to turn OFF during listening
            if _hotkey_toggle_event.is_set():
                _hotkey_toggle_event.clear()
                _is_active = False
                break

            # 3. Handle NO SPEECH (Silence)
            if not cmd or not cmd.strip():
                # STATE: IDLE — Jarvis quietly waits for speech; NEVER shuts down!
                safe_ui_update("Jarvis Online 🟢", "#10b981")
                time.sleep(0.08)
                continue

            # 4. User spoke! Clean any optional leading wake prefix
            clean_cmd = cmd.strip()
            for prefix in ("hey jarvis", "hi jarvis", "jarvis", "हे जार्विस", "जार्विस", "hey jervis", "jervis"):
                if clean_cmd.lower().startswith(prefix):
                    clean_cmd = clean_cmd[len(prefix):].strip(",- ")
            if not clean_cmd:
                clean_cmd = cmd.strip()

            # Check for explicit verbal shutdown
            if clean_cmd.lower() in ("shutdown jarvis", "turn off jarvis", "deactivate jarvis", "stop jarvis", "exit jarvis"):
                _is_active = False
                break

            # 5. STATE: PROCESSING
            safe_ui_update("Thinking... 🧠", "#f59e0b")
            print(f"[STATE] PROCESSING: '{clean_cmd}'")
            reply, should_exit = commands.handle_command(clean_cmd)

            # Check if hotkey was pressed to turn OFF during processing
            if _hotkey_toggle_event.is_set():
                _hotkey_toggle_event.clear()
                _is_active = False
                break

            # 6. STATE: SPEAKING
            safe_ui_update("Speaking... 💬", "#a855f7")
            print(f"[STATE] SPEAKING: '{reply}'")
            voice.speak(reply)

            if should_exit is True:
                _is_active = False
                break

            # Check if hotkey was pressed to turn OFF during speech
            if _hotkey_toggle_event.is_set():
                _hotkey_toggle_event.clear()
                _is_active = False
                break

            # 7. Return to LISTENING / IDLE for natural continuous conversation
            safe_ui_update("Listening... 🎙️", "#22d3ee")

        # STATE: TURNING OFF
        voice.stop_speaking()
        voice.play_audio_cue("standby")
        safe_ui_update("Jarvis Offline 🔴", "#ef4444")
        voice.speak("Jarvis offline.")
        session_context.context.clear()
        safe_ui_hide()
        _is_active = False
        print("[STATE] OFF — Jarvis is dormant. Press [Ctrl + Alt + J] to start.")


def start():
    acquire_instance_lock()
    global ui_app
    ui_app = VoiceIndicatorUI()
    threading.Thread(target=assistant_loop, daemon=True).start()
    ui_app.root.mainloop()


if __name__ == "__main__":
    start()

"""
main.py – J.A.R.V.I.S Background Engine with Ignition & Standby Lifecycle.

Lifecycle:
  1. STANDBY (Silent Background):
     - Auto-starts on Windows boot (via start_jarvis.vbs / Startup shortcut).
     - Waits silently for "Hey Jarvis" OR global hotkey `Ctrl+Alt+J` (ignition).
  2. ACTIVE (Ignited):
     - Once ignited, you only need to say "Jarvis <command>" (e.g. "Jarvis open Spotify").
     - Does NOT self-trigger on background noise or silence.
  3. RETURN TO STANDBY:
     - Saying "goodbye Jarvis", "bye Jarvis", "Jarvis jao", or "standby" returns to silent background mode.
"""

import os
import sys
import time
import socket
import threading
import tkinter as tk
import voice_engine as voice
import commands

INSTANCE_PORT = 48123
_instance_socket = None
_hotkey_ignited = threading.Event()


def acquire_instance_lock():
    global _instance_socket
    _instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _instance_socket.bind(("127.0.0.1", INSTANCE_PORT))
    except OSError:
        print("[Jarvis Alert] Another instance of Jarvis is already running.")
        sys.exit(0)


def _start_global_hotkey_listener():
    """Registers Ctrl+Alt+J as an optional instant ignition shortcut."""
    try:
        import keyboard
        keyboard.add_hotkey("ctrl+alt+j", lambda: _hotkey_ignited.set())
        print("[Jarvis] Global Ignition Hotkey active: Ctrl+Alt+J")
    except Exception:
        pass


class VoiceIndicatorUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.93)
        self.root.config(bg="#06101b")

        screen_width = self.root.winfo_screenwidth()
        width, height = 340, 52
        x = (screen_width - width) // 2
        y = 26
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.label = tk.Label(
            self.root,
            text="Listening for wake word...",
            fg="#22d3ee",
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
    voice.calibrate()
    _start_global_hotkey_listener()

    print("\n==================================================")
    print(" [J.A.R.V.I.S] Online in Silent Standby Mode")
    print("  • Ignition: Say 'Hey Jarvis' or press Ctrl+Alt+J")
    print("  • Active:   Say 'Jarvis <command>'")
    print("  • Sleep:    Say 'Goodbye Jarvis' or 'Jarvis jao'")
    print("==================================================\n")

    STATE_STANDBY = 0
    STATE_ACTIVE = 1
    state = STATE_STANDBY

    while True:
        # 1. STANDBY: Wait for "Hey Jarvis" or Ctrl+Alt+J ignition
        if state == STATE_STANDBY:
            if _hotkey_ignited.is_set():
                _hotkey_ignited.clear()
                heard_wake, immediate_cmd = True, ""
                voice.play_audio_cue("wake")
            else:
                heard_wake, immediate_cmd = voice.listen_for_wake_word(session_active=False)

            if not heard_wake:
                continue

            state = STATE_ACTIVE
            if not immediate_cmd:
                safe_ui_update("Listening... 🎙️", "#22d3ee")
                voice.speak(
                    "Online and ready, sir.",
                    on_start=lambda: safe_ui_update("Speaking... 💬", "#a855f7"),
                    on_end=lambda: safe_ui_update("Listening... 🎙️", "#22d3ee"),
                )
                immediate_cmd = voice.listen_for_command(timeout=5.0)

            if immediate_cmd:
                if voice.is_standby_command(immediate_cmd):
                    voice.play_audio_cue("standby")
                    safe_ui_hide()
                    state = STATE_STANDBY
                    continue

                safe_ui_update("Thinking... 🧠", "#f59e0b")
                reply, should_exit = commands.handle_command(immediate_cmd)
                safe_ui_update("Speaking... 💬", "#a855f7")
                voice.speak(reply)

                if should_exit:
                    os._exit(0)
                safe_ui_update("Active (Say 'Jarvis ...')", "#10b981")

        # 2. ACTIVE: Requires "Jarvis <command>" (never triggers on random silence)
        elif state == STATE_ACTIVE:
            if _hotkey_ignited.is_set():
                _hotkey_ignited.clear()
                safe_ui_update("Listening... 🎙️", "#22d3ee")
                cmd = voice.listen_for_command(timeout=5.0)
                heard_wake = bool(cmd)
            else:
                heard_wake, cmd = voice.listen_for_wake_word(session_active=True)

            if not heard_wake:
                continue

            if cmd == "__STANDBY__" or voice.is_standby_command(cmd):
                voice.play_audio_cue("standby")
                voice.speak("Going to standby, sir.")
                safe_ui_hide()
                state = STATE_STANDBY
                continue

            if not cmd:
                safe_ui_update("Listening... 🎙️", "#22d3ee")
                voice.play_audio_cue("wake")
                cmd = voice.listen_for_command(timeout=5.0)

            if not cmd:
                safe_ui_update("Active (Say 'Jarvis ...')", "#10b981")
                continue

            safe_ui_update("Thinking... 🧠", "#f59e0b")
            reply, should_exit = commands.handle_command(cmd)
            safe_ui_update("Speaking... 💬", "#a855f7")
            voice.speak(reply)

            if should_exit:
                os._exit(0)
            safe_ui_update("Active (Say 'Jarvis ...')", "#10b981")


def start():
    acquire_instance_lock()
    global ui_app
    ui_app = VoiceIndicatorUI()
    threading.Thread(target=assistant_loop, daemon=True).start()
    ui_app.root.mainloop()


if __name__ == "__main__":
    start()
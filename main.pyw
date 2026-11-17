"""
main.py – J.A.R.V.I.S Shortcut Key Edition (Ctrl + Alt + J).

Control Lifecycle:
  1. DORMANT / CLOSED (Zero-Resource Background):
     - Jarvis starts quietly in the background on Windows boot or manual start.
     - The microphone is completely OFF (no passive listening, zero CPU usage, no false triggers).
     - Waits ONLY for the global shortcut: Ctrl + Alt + J.
  2. START / ACTIVATE (Ctrl + Alt + J):
     - Pressing Ctrl + Alt + J instantly wakes Jarvis.
     - Plays futuristic wake chime.
     - Displays floating HUD: "Listening... 🎙️".
     - Immediately captures your voice directive (no wake word needed!).
     - Preserves all UI modes:
         * "Listening... 🎙️" (#22d3ee)
         * "Thinking... 🧠" (#f59e0b)
         * "Speaking... 💬" (#a855f7)
     - Jarvis answers aloud with his expressive bilingual voice.
  3. CLOSE / DEACTIVATE (Ctrl + Alt + J):
     - Pressing Ctrl + Alt + J while Jarvis is active closes him immediately.
     - Stops listening, cuts off any speech playback, plays close chime, hides HUD.
     - Returns to completely dormant background state.
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
    Registers Ctrl+Alt+J using both the keyboard hook AND the native Win32 RegisterHotKey API
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
        width, height = 340, 52
        x = (screen_width - width) // 2
        y = 26
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.label = tk.Label(
            self.root,
            text="Listening... 🎙️",
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
    global _is_active
    voice.calibrate()
    _start_global_hotkey_listener()

    print("\n==================================================")
    print(" [J.A.R.V.I.S] Shortcut Key Edition Online")
    print("  • START: Press [Ctrl + Alt + J] to start listening")
    print("  • CLOSE: Press [Ctrl + Alt + J] to close/stop")
    print("  • No wake words or passive standby listening.")
    print("==================================================\n")

    while True:
        # DORMANT STATE: Wait silently until the user presses Ctrl + Alt + J
        _hotkey_toggle_event.wait()
        _hotkey_toggle_event.clear()

        # START ACTIVATION
        _is_active = True
        voice.play_audio_cue("wake")
        safe_ui_update("Listening... 🎙️", "#22d3ee")
        print("[Jarvis] Started via shortcut. Listening for your directive...")

        while _is_active:
            # Check if user pressed Ctrl+Alt+J to CLOSE before/during listening
            if _hotkey_toggle_event.is_set():
                _hotkey_toggle_event.clear()
                _is_active = False
                break

            # Listen for user command directly (no wake word required!)
            cmd = voice.listen_for_command(timeout=6.0, phrase_time_limit=12.0)

            # Check if user pressed Ctrl+Alt+J to CLOSE while speaking/listening
            if _hotkey_toggle_event.is_set():
                _hotkey_toggle_event.clear()
                _is_active = False
                break

            if not cmd or not cmd.strip():
                # Silence timeout after speaking -> prompt user or auto-close
                safe_ui_update("Ready (Ctrl+Alt+J to close) 🟢", "#10b981")
                # Wait up to 8 seconds for follow-up speech or close hotkey
                t_start = time.time()
                while time.time() - t_start < 8.0:
                    if _hotkey_toggle_event.is_set():
                        _hotkey_toggle_event.clear()
                        _is_active = False
                        break
                    time.sleep(0.2)
                _is_active = False
                break

            # Clean any legacy "Hey Jarvis" prefix if user said it out of habit
            clean_cmd = cmd.strip()
            for prefix in ("hey jarvis", "hi jarvis", "jarvis", "हे जार्विस", "जार्विस", "hey jervis"):
                if clean_cmd.lower().startswith(prefix):
                    clean_cmd = clean_cmd[len(prefix):].strip(",- ")
            if not clean_cmd:
                clean_cmd = cmd.strip()

            # Check if user asked to sleep or exit
            if clean_cmd.lower() in ("goodbye", "bye", "sleep", "exit", "quit", "close"):
                _is_active = False
                break

            # 1. THINKING MODE
            safe_ui_update("Thinking... 🧠", "#f59e0b")
            print(f"[Jarvis] Thinking on: '{clean_cmd}'")
            reply, should_exit = commands.handle_command(clean_cmd)

            # Check if hotkey was pressed to close during thinking
            if _hotkey_toggle_event.is_set():
                _hotkey_toggle_event.clear()
                _is_active = False
                break

            # 2. SPEAKING MODE
            safe_ui_update("Speaking... 💬", "#a855f7")
            print(f"[Jarvis] Replying: '{reply}'")
            voice.speak(reply)

            if should_exit:
                os._exit(0)

            # Check if hotkey was pressed during speaking
            if _hotkey_toggle_event.is_set():
                _hotkey_toggle_event.clear()
                _is_active = False
                break

            # Prompt for follow-up
            safe_ui_update("Listening... 🎙️", "#22d3ee")

        # CLOSE / SHUT DOWN TO DORMANT
        voice.stop_speech()
        voice.play_audio_cue("standby")
        safe_ui_hide()
        _is_active = False
        print("[Jarvis] Closed. Press [Ctrl + Alt + J] whenever you need me.")


def start():
    acquire_instance_lock()
    global ui_app
    ui_app = VoiceIndicatorUI()
    threading.Thread(target=assistant_loop, daemon=True).start()
    ui_app.root.mainloop()


if __name__ == "__main__":
    start()

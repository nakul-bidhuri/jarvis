"""
main.py — Jarvis's entry point with a sleek, taskbar-free Tkinter HUD.
"""

import tkinter as tk
import threading
import time
import os
import sys
import socket
import voice_engine as voice
import commands

# ---------- Single-Instance Lock (Prevents Double Voice & Conflicts) ----------

INSTANCE_PORT = 48123
_instance_socket = None

def acquire_instance_lock():
    global _instance_socket
    _instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _instance_socket.bind(('127.0.0.1', INSTANCE_PORT))
    except OSError:
        print("\n[Jarvis Alert] Another instance of Jarvis is already running!")
        print("To prevent double voices and mic lag, only one instance is allowed.")
        print("If you want to stop background instances, run: stop_jarvis.bat\n")
        sys.exit(0)

class VoiceIndicatorUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Jarvis")
        
        # Borderless HUD floating at the top, hidden from the taskbar
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)  # Slight transparency
        self.root.config(bg="#121212")

        screen_width = self.root.winfo_screenwidth()
        width, height = 320, 52
        x = (screen_width - width) // 2
        y = 30
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.label = tk.Label(
            self.root, 
            text="Waiting...", 
            fg="#00FFCC", 
            bg="#121212", 
            font=("Segoe UI", 13, "bold")
        )
        self.label.pack(expand=True, fill="both")
        
        # Start hidden until wake word activates
        self.root.withdraw()

    def show(self, text, color):
        self.label.config(text=text, fg=color)
        self.root.deiconify()
        self.root.update()

    def hide(self):
        self.root.withdraw()

ui_app = None

# --- Thread-Safe UI updaters ---
def safe_ui_update(text, color):
    """Safely updates the Tkinter UI from the background voice thread."""
    if ui_app and ui_app.root:
        ui_app.root.after(0, ui_app.show, text, color)

def safe_ui_hide():
    if ui_app and ui_app.root:
        ui_app.root.after(0, ui_app.hide)

# --- Main Voice Loop with Car-Key Ignition & Sleep Protection ---
def assistant_loop():
    voice.calibrate()
    print("\n=======================================================")
    print(" [Jarvis 2.0 AI Assistant - Car-Key Ignition System]")
    print(" Current State: LOCKED / DORMANT (Mic Inactive)")
    print(" 🔑 Press [Ctrl + Alt + J] to ignite into STANDBY mode.")
    print(" In Standby, say 'Hey Jarvis' to activate systems.")
    print("=======================================================\n")

    def on_hotkey_toggle():
        curr = voice.get_system_state()
        if curr == voice.STATE_LOCKED:
            voice.set_system_state(voice.STATE_STANDBY)
            safe_ui_update("🟡 Standby (Say 'Hey Jarvis')", "#F59E0B")
            voice.speak("Ignition confirmed. Jarvis in standby. Say 'Hey Jarvis' to activate.")
        else:
            voice.set_system_state(voice.STATE_LOCKED)
            safe_ui_update("🔒 Locked (Press Ctrl+Alt+J)", "#EF4444")
            voice.speak("Jarvis locked down.")
            time.sleep(1.2)
            safe_ui_hide()

    def on_sleep_wake():
        voice.set_system_state(voice.STATE_LOCKED, announce=False)
        safe_ui_update("🔒 Locked (Press Ctrl+Alt+J)", "#EF4444")
        time.sleep(1.5)
        safe_ui_hide()

    # Register Global Windows Hotkey Ctrl+Alt+J & Sleep Monitor
    voice.start_global_hotkey_listener(on_hotkey_toggle)
    voice.start_sleep_monitor(on_sleep_wake)

    # Initial UI notice
    safe_ui_update("🔒 Locked (Press Ctrl+Alt+J)", "#EF4444")
    time.sleep(1.8)
    safe_ui_hide()

    while True:
        state = voice.get_system_state()

        # State 1: Locked — zero mic listening, waiting for Ctrl+Alt+J
        if state == voice.STATE_LOCKED:
            time.sleep(0.2)
            continue

        # State 2: Standby — strictly waiting for 'Hey Jarvis'
        if state == voice.STATE_STANDBY:
            safe_ui_update("🟡 Standby (Say 'Hey Jarvis')", "#F59E0B")
            heard_wake, immediate_cmd = voice.listen_for_wake_word(session_active=False)
            if not heard_wake:
                continue

            # 'Hey Jarvis' ignited! Transition to ACTIVE
            voice.set_system_state(voice.STATE_ACTIVE, announce=False)
            safe_ui_update("🟢 Active (Say 'Jarvis...')", "#00FFCC")

            command_to_process = immediate_cmd
            if not command_to_process:
                greeting = "Jarvis online and ready. How may I assist you, Nakul?"
                voice.speak(
                    greeting,
                    on_start=lambda: safe_ui_update("Speaking... 💬", "#B026FF"),
                    on_end=lambda: safe_ui_update("Listening... 🎙️", "#00FFCC")
                )

            # State 3: Active Dialogue Loop
            active = True
            idle_ticks = 0
            while active and voice.get_system_state() == voice.STATE_ACTIVE:
                if command_to_process:
                    command_text = command_to_process
                    command_to_process = ""
                else:
                    command_text = voice.listen_for_command()

                if not command_text:
                    idle_ticks += 1
                    if idle_ticks >= 2:  # Return to Standby after 2 silences
                        voice.set_system_state(voice.STATE_STANDBY, announce=False)
                        safe_ui_update("🟡 Standby (Say 'Hey Jarvis')", "#F59E0B")
                        time.sleep(1.0)
                        safe_ui_hide()
                        break
                    continue

                idle_ticks = 0

                # Check explicit Standby / Sleep command
                clean_cmd = command_text.lower().strip()
                if any(s in clean_cmd for s in ["standby", "go to sleep", "sleep", "सो जाओ", "शांत रहो"]):
                    voice.set_system_state(voice.STATE_STANDBY, announce=False)
                    safe_ui_update("🟡 Standby (Say 'Hey Jarvis')", "#F59E0B")
                    voice.speak("Returning to standby mode.")
                    time.sleep(1.0)
                    safe_ui_hide()
                    break

                # AI Processing state (Orange)
                safe_ui_update("Thinking... 🧠", "#FFB300")

                # Execute command with Gemini
                reply, should_exit = commands.handle_command(command_text)

                # AI Speaking state (Violet)
                safe_ui_update("Speaking... 💬", "#B026FF")
                voice.speak(reply, on_end=lambda: None)

                if should_exit is True:
                    safe_ui_update("Goodbye! 👋", "#FF3366")
                    print("[Jarvis] Shutdown requested. Exiting...")
                    time.sleep(1.2)
                    if ui_app and ui_app.root:
                        try:
                            ui_app.root.quit()
                            ui_app.root.destroy()
                        except Exception:
                            pass
                    os._exit(0)

                # Keep in active mode for follow-up questions until silence or standby
                safe_ui_update("🟢 Active (Listening...)", "#00FFCC")

def start():
    acquire_instance_lock()
    global ui_app
    ui_app = VoiceIndicatorUI()
    
    # Run voice engine in a background daemon thread
    threading.Thread(target=assistant_loop, daemon=True).start()
    
    # Start Tkinter main loop on main thread
    ui_app.root.mainloop()

if __name__ == "__main__":
    start()

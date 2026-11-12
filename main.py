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

# --- Main Voice Loop ---
def assistant_loop():
    voice.calibrate()
    print("\n=======================================================")
    print(" [Jarvis 2.0 AI Assistant is Online]")
    print(" Nakul's AI Mentor & System Assistant")
    print(" Say 'Hey Jarvis' or 'Hey Jarvis <command>' to begin.")
    print(" Example commands:")
    print("   * 'Hey Jarvis, open WhatsApp and open Mom's chat'")
    print("   * 'Hey Jarvis, search Google for who is Elon Musk'")
    print("   * 'Hey Jarvis, open UPES portal'")
    print("   * 'Hey Jarvis, open notepad and write I am doing BTEC'")
    print("=======================================================\n")

    while True:
        heard_wake, immediate_cmd = voice.listen_for_wake_word()
        if not heard_wake:
            continue

        active = True
        command_to_process = immediate_cmd

        # If the user only said 'Hey Jarvis', acknowledge verbally like Siri
        if not command_to_process:
            safe_ui_update("Listening... 🎙️", "#00FFCC")
            voice.speak(
                "Yes?", 
                on_start=lambda: safe_ui_update("Speaking... 💬", "#B026FF"),
                on_end=lambda: safe_ui_update("Listening... 🎙️", "#00FFCC")
            )

        idle_ticks = 0
        while active:
            # If the user gave wake word + command in one breath, process immediately!
            if command_to_process:
                command_text = command_to_process
                command_to_process = ""
            else:
                command_text = voice.listen_for_command()
            
            if not command_text:
                idle_ticks += 1
                if idle_ticks >= 2:   # Return to standby after silence
                    active = False
                    break
                continue

            idle_ticks = 0
            
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

            # Alexa Silent Lifecycle: After executing any command, immediately drop to silent standby
            active = False
            break

        safe_ui_hide()

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

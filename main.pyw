"""
main.pyw — Jarvis's entry point with a sleek, taskbar-free Tkinter HUD (windowless runner).
"""

import tkinter as tk
import threading
import time
import os
import sys
import socket
import voice_engine as voice
import commands

INSTANCE_PORT = 48123
_instance_socket = None

def acquire_instance_lock():
    global _instance_socket
    _instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _instance_socket.bind(('127.0.0.1', INSTANCE_PORT))
    except OSError:
        sys.exit(0)

class VoiceIndicatorUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Jarvis")
        
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)
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
        
        self.root.withdraw()

    def show(self, text, color):
        self.label.config(text=text, fg=color)
        self.root.deiconify()
        self.root.update()

    def hide(self):
        self.root.withdraw()

ui_app = None

def safe_ui_update(text, color):
    if ui_app and ui_app.root:
        ui_app.root.after(0, ui_app.show, text, color)

def safe_ui_hide():
    if ui_app and ui_app.root:
        ui_app.root.after(0, ui_app.hide)

def assistant_loop():
    voice.calibrate()

    while True:
        heard_wake, immediate_cmd = voice.listen_for_wake_word()
        if not heard_wake:
            continue

        active = True
        command_to_process = immediate_cmd

        if not command_to_process:
            safe_ui_update("Listening... 🎙️", "#00FFCC")
            voice.speak(
                "Yes?", 
                on_start=lambda: safe_ui_update("Speaking... 💬", "#B026FF"),
                on_end=lambda: safe_ui_update("Listening... 🎙️", "#00FFCC")
            )

        idle_ticks = 0
        while active:
            if command_to_process:
                command_text = command_to_process
                command_to_process = ""
            else:
                command_text = voice.listen_for_command()
            
            if not command_text:
                idle_ticks += 1
                if idle_ticks >= 2:
                    active = False
                    break
                continue

            idle_ticks = 0
            safe_ui_update("Thinking... 🧠", "#FFB300") 

            reply, should_exit = commands.handle_command(command_text)

            safe_ui_update("Speaking... 💬", "#B026FF")
            voice.speak(reply, on_end=lambda: None)

            if should_exit is True:
                safe_ui_update("Goodbye! 👋", "#FF3366")
                time.sleep(1.2)
                if ui_app and ui_app.root:
                    try:
                        ui_app.root.quit()
                        ui_app.root.destroy()
                    except Exception:
                        pass
                os._exit(0)

            if should_exit == "sleep":
                active = False
                break

            safe_ui_update("Listening... 🎙️", "#00FFCC")

        safe_ui_hide()

def start():
    acquire_instance_lock()
    global ui_app
    ui_app = VoiceIndicatorUI()
    threading.Thread(target=assistant_loop, daemon=True).start()
    ui_app.root.mainloop()

if __name__ == "__main__":
    start()

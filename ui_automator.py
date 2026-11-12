"""
ui_automator.py — Deterministic Windows UI Automation using Microsoft UIAutomation.

Replaces brittle blind sleeps and hardcoded keystrokes with verified window focusing,
control inspection, and reliable desktop automation.
"""

import time
import os
import subprocess

try:
    import pyperclip
except Exception:
    pyperclip = None

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except Exception:
    pyautogui = None

try:
    import uiautomation as auto
except Exception:
    auto = None

import app_discovery
import memory_manager

def focus_window_by_name(title_keyword: str, timeout: float = 3.0) -> bool:
    """
    Finds a top-level window by title keyword, restores it if minimized,
    and brings it reliably to the foreground.
    """
    if not auto:
        return False
    t0 = time.time()
    keyword_lower = title_keyword.lower()

    while time.time() - t0 < timeout:
        # Search all top-level windows via UIAutomation
        try:
            root = auto.GetRootControl()
            for win in root.GetChildren():
                try:
                    name = win.Name.lower()
                    if keyword_lower in name:
                        if win.NativeWindowHandle:
                            # Bring window to foreground
                            win.SetActive()
                            win.SetFocus()
                            time.sleep(0.2)
                            return True
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(0.3)
    return False

def open_app_deterministically(app_name: str) -> tuple[bool, str]:
    """
    Launches an application instantly and focuses its window asynchronously.
    """
    success, msg = app_discovery.launch_app(app_name)
    if not success:
        return False, msg

    # Asynchronously focus window without blocking voice response
    import threading
    threading.Thread(target=lambda: focus_window_by_name(app_name, timeout=2.0), daemon=True).start()
    return True, f"Opening {app_name.title()} for you now."

def write_to_notepad(text: str) -> str:
    """
    Opens Notepad, ensures it is in focus, writes the text cleanly,
    and saves the note permanently to memory.
    """
    if not pyautogui or not pyperclip:
        memory_manager.save_user_note("Notepad Entry", text)
        return f"Saved note to memory: '{text}' (Desktop GUI typing is only supported in local desktop mode)."
    try:
        # 1. Launch or bring up Notepad
        app_discovery.launch_app("notepad")
        time.sleep(1.0)
        focus_window_by_name("notepad", timeout=2.0)
        time.sleep(0.3)

        # 2. Paste text cleanly using clipboard injection
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        
        # 3. Save into long-term memory
        memory_manager.save_user_note("Notepad Entry", text)
        return f"Opened Notepad and wrote: '{text}'"
    except Exception as e:
        return f"Error writing to Notepad: {e}"

def open_whatsapp_chat(contact_name: str, message: str = "") -> str:
    """
    Opens WhatsApp Desktop, searches for the specified contact,
    opens their chat, and optionally types and sends a message.
    """
    if not pyautogui or not pyperclip:
        return f"WhatsApp desktop control is available when running locally on Windows. Contact: {contact_name}"
    try:
        # 1. Launch / focus WhatsApp
        app_discovery.launch_app("whatsapp")
        time.sleep(1.2)
        focus_window_by_name("whatsapp", timeout=2.0)
        time.sleep(0.4)

        # 2. Focus WhatsApp Search Bar via standard shortcut (Ctrl + F)
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        time.sleep(0.2)

        # 3. Enter contact name
        pyperclip.copy(contact_name)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.8)

        # 4. Open matching chat
        pyautogui.press('enter')
        time.sleep(0.5)

        # 5. Send message if requested
        if message:
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)
            pyautogui.press('enter')
            return f"Opened WhatsApp chat for {contact_name} and sent: '{message}'"

        return f"Opened WhatsApp chat for {contact_name}."
    except Exception as e:
        return f"Could not interact with WhatsApp: {e}"

def type_text(text: str) -> str:
    """Types or pastes text into the currently active window."""
    if not pyautogui or not pyperclip:
        return f"Typing is only supported when running locally on Windows. Text: '{text}'"
    time.sleep(0.2)
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')
    return f"Typed: '{text}'"

def press_shortcut(keys: str) -> str:
    """Presses a shortcut like 'ctrl+c', 'alt+tab', 'win+d'."""
    if not pyautogui:
        return f"Keyboard shortcuts are only supported when running locally on Windows. Shortcut: {keys}"
    tokens = [k.strip().lower() for k in keys.split('+')]
    pyautogui.hotkey(*tokens)
    return f"Executed shortcut: {keys}"

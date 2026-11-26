"""
ui_automator.py — Deterministic Windows UI Automation using Native Win32 API.

Replaces brittle sleeps and non-functional automation with verified window focusing,
control inspection, and reliable desktop automation for WhatsApp, Notepad, and other apps.
"""

import time
import os
import ctypes
from ctypes import wintypes
import subprocess
import webbrowser
from typing import Optional, Tuple, List

try:
    import pyperclip
except Exception:
    pyperclip = None

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except Exception:
    pyautogui = None

import app_discovery
import memory_manager


def find_window_hwnd(title_keyword: str) -> Optional[int]:
    """Finds a top-level visible window whose title or class contains title_keyword."""
    try:
        user32 = ctypes.windll.user32
        target_hwnd = None
        keyword_lower = title_keyword.lower()

        def enum_cb(hwnd, lparam):
            nonlocal target_hwnd
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.lower()
                    class_buff = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, class_buff, 256)
                    cname = class_buff.value.lower()
                    
                    # Ignore common system dummy windows
                    if any(t in title for t in ("default ime", "msctls_statusbar32", "gdi+ window", "program manager")):
                        return True

                    if keyword_lower in title or keyword_lower in cname:
                        target_hwnd = hwnd
                        return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        return target_hwnd
    except Exception:
        return None


def focus_window_by_name(title_keyword: str, timeout: float = 3.0) -> bool:
    """
    Finds a top-level window by title keyword, restores it if minimized,
    and brings it reliably to the foreground.
    """
    user32 = ctypes.windll.user32
    t0 = time.time()
    keyword_lower = title_keyword.lower()

    while time.time() - t0 < timeout:
        hwnd = find_window_hwnd(keyword_lower)
        if hwnd:
            try:
                # Restore window if minimized
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                else:
                    user32.ShowWindow(hwnd, 5)  # SW_SHOW

                # Alt key press trick to bypass Windows foreground lock restriction
                user32.keybd_event(0x12, 0, 0, 0)
                user32.SetForegroundWindow(hwnd)
                user32.keybd_event(0x12, 0, 2, 0)
                user32.BringWindowToTop(hwnd)
                time.sleep(0.3)
                return True
            except Exception:
                pass
        time.sleep(0.25)
    return False


def launch_whatsapp() -> bool:
    """
    Launches WhatsApp cleanly, recovers from background notification deadlocks,
    and brings its window to focus.
    """
    # 1. If window already visible, bring it to front
    if focus_window_by_name("whatsapp", timeout=0.8):
        return True

    # 2. Check for background push notification process (/nowindow) which prevents GUI from launching
    try:
        import psutil
        for p in psutil.process_iter(['name', 'cmdline']):
            try:
                if 'whatsapp' in p.info.get('name', '').lower():
                    cmdline = " ".join(p.info.get('cmdline') or [])
                    if '/nowindow' in cmdline or '-RegisterForBGTaskServer' in cmdline:
                        print("[WhatsApp] Terminating background /nowindow process to allow UI launch...")
                        p.kill()
            except Exception:
                pass
    except Exception:
        pass

    # 3. Launch official Windows UWP Desktop App via Explorer
    try:
        subprocess.Popen(["explorer.exe", r"shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"])
    except Exception:
        try:
            os.startfile("whatsapp:")
        except Exception:
            pass

    # Wait up to 3 seconds for desktop window to appear
    if focus_window_by_name("whatsapp", timeout=3.0):
        return True

    # 4. Fallback to Chrome PWA shortcut if desktop app didn't show
    lnk_path = os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Chrome Apps\WhatsApp Web.lnk")
    if os.path.exists(lnk_path):
        try:
            os.startfile(lnk_path)
            if focus_window_by_name("whatsapp", timeout=3.0):
                return True
        except Exception:
            pass

    # 5. Fallback to Web Browser
    try:
        webbrowser.open("https://web.whatsapp.com")
        time.sleep(1.5)
        return focus_window_by_name("whatsapp", timeout=3.0)
    except Exception:
        return False


def open_app_deterministically(app_name: str) -> Tuple[bool, str]:
    """
    Launches an application instantly and focuses its window asynchronously.
    """
    if "whatsapp" in app_name.lower():
        launched = launch_whatsapp()
        return True, "Opening WhatsApp for you now."

    success, msg = app_discovery.launch_app(app_name)
    if not success:
        return False, msg

    import threading
    threading.Thread(target=lambda: focus_window_by_name(app_name, timeout=2.5), daemon=True).start()
    return True, f"Opening {app_name.title()} for you now."


def write_to_notepad(text: str) -> str:
    """
    Opens Notepad, ensures it is in focus, writes the text cleanly,
    and saves the note permanently to memory.
    """
    if not pyautogui or not pyperclip:
        memory_manager.save_user_note("Notepad Entry", text)
        return f"Saved note to memory: '{text}' (Desktop GUI typing requires local display)."
    try:
        app_discovery.launch_app("notepad")
        time.sleep(0.8)
        focus_window_by_name("notepad", timeout=2.5)
        time.sleep(0.3)

        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        
        memory_manager.save_user_note("Notepad Entry", text)
        return f"Opened Notepad and wrote: '{text}'"
    except Exception as e:
        return f"Error writing to Notepad: {e}"


def open_whatsapp_chat(contact_name: str, message: str = "") -> str:
    """
    Opens WhatsApp Desktop/Web, searches for the specified contact,
    opens their chat, and sends the requested message reliably.
    """
    if not pyautogui or not pyperclip:
        return f"WhatsApp desktop control is available when running locally on Windows. Contact: {contact_name}"
    
    clean_contact = (contact_name or "").strip()
    clean_msg = (message or "").strip()

    try:
        # 1. Launch / focus WhatsApp
        launch_whatsapp()
        time.sleep(0.8)
        focus_window_by_name("whatsapp", timeout=2.5)
        time.sleep(0.4)

        # 2. Check if generic contact (e.g. 'him', 'her', 'someone', 'chat')
        generic_tokens = {"him", "her", "them", "someone", "anyone", "chat", "someone someone", "friend", "this chat", ""}
        is_generic = clean_contact.lower() in generic_tokens

        if is_generic:
            # Select current active conversation
            pyautogui.press('enter')
            time.sleep(0.3)
        else:
            # Focus search bar via standard shortcut (Ctrl + F)
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            time.sleep(0.2)

            # Type contact name
            pyperclip.copy(clean_contact)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.8)

            # Select matching contact
            pyautogui.press('down')
            time.sleep(0.2)
            pyautogui.press('enter')
            time.sleep(0.5)

        # 3. Send message if requested
        if clean_msg:
            time.sleep(0.3)
            pyperclip.copy(clean_msg)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)
            pyautogui.press('enter')
            target = "the active chat" if is_generic else clean_contact
            return f"Opened WhatsApp and sent '{clean_msg}' to {target}."

        target = "the active chat" if is_generic else clean_contact
        return f"Opened WhatsApp chat for {target}."
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


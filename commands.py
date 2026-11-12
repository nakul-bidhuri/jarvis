"""
commands.py — Agentic Orchestrator & Command Handler for Jarvis 2.0.

Powered by:
  - Universal Windows App Discovery (170+ apps via Windows Shell)
  - Deterministic Windows UIAutomation (UIA)
  - Autonomous Multi-Tool Calling with Gemini 3.5 Flash Lite
  - Dedicated WhatsApp, Notepad, and UPES College Portal automation
  - Data Science & Tech Career Mentor for Nakul
  - Permanent Long-term Memory
"""

import os
import string
import time
import imaplib
import email
from email.header import decode_header
from google import genai

import config
import memory_manager
import app_discovery
import ui_automator
import web_search_agent
import college_portal
import spotify_control
import music_player
import laptop_controller
import audio_cues
import live_knowledge
import reminder_scheduler
import daily_briefing
import safe_messaging

# ---------- Spatial OS Knowledge, News, Weather & Assistant Tools ----------

def get_live_weather(location: str = "Dehradun") -> str:
    """Fetches real-time weather conditions, temperature, humidity, and forecast for any city (defaults to Dehradun)."""
    return live_knowledge.get_live_weather(location)

def get_live_news(topic: str = "") -> str:
    """Fetches live breaking news or topic headlines from Google News RSS."""
    return live_knowledge.get_live_news(topic)

def search_live_knowledge(query: str) -> str:
    """Directly queries Wikipedia and DuckDuckGo to extract instant factual answers for technical, general, and historical questions."""
    return live_knowledge.search_live_knowledge(query)

def get_github_overview(repo_or_user: str) -> str:
    """Retrieves public repository metrics, star counts, primary languages, and descriptions from GitHub."""
    return live_knowledge.get_github_overview(repo_or_user)

def generate_daily_briefing() -> str:
    """Summarizes current time, local Dehradun weather, scheduled reminders, laptop battery/telemetry, and top headlines."""
    return daily_briefing.generate_daily_briefing()

def add_reminder(reminder_text: str, time_spec: str) -> str:
    """Schedules a new reminder for the user (e.g. 'call Rahul', 'at 6 PM' or 'in 15 minutes')."""
    return reminder_scheduler.add_reminder(reminder_text, time_spec)

def list_active_reminders() -> str:
    """Returns a list of all active pending reminders scheduled by the user."""
    return reminder_scheduler.list_active_reminders()

def cancel_reminder(search_query: str) -> str:
    """Cancels a scheduled reminder by keyword or ID."""
    return reminder_scheduler.cancel_reminder(search_query)

def stage_whatsapp_message(recipient: str, message: str) -> str:
    """Stages an outgoing WhatsApp message and asks user for verbal confirmation ('Should I send it?') before dispatching."""
    return safe_messaging.stage_message("WhatsApp", recipient, message)

def confirm_and_send_message() -> str:
    """Confirms and dispatches any staged pending WhatsApp or email message after explicit user permission."""
    return safe_messaging.confirm_and_dispatch()

def cancel_pending_message() -> str:
    """Cancels the currently staged message without sending anything."""
    return safe_messaging.cancel_staged_message()

def take_screenshot(custom_name: str = "") -> str:
    """Captures the laptop screen and saves it as a high-resolution PNG on the Desktop."""
    return laptop_controller.take_screenshot(custom_name)

def read_clipboard() -> str:
    """Reads current text content from the Windows clipboard."""
    return laptop_controller.read_clipboard()

def copy_to_clipboard(text: str) -> str:
    """Copies the specified text into the Windows clipboard."""
    return laptop_controller.copy_to_clipboard(text)

def open_code_editor(target_path: str = "") -> str:
    """Opens Visual Studio Code (VS Code) at the specified directory or project."""
    return laptop_controller.open_code_editor(target_path)

# ---------- Mail ----------

def read_recent_mail(count: int = 5) -> str:
    """Reads the user's most recent unread emails from their Gmail inbox."""
    address = config.get("gmail_address")
    app_pw = config.get("gmail_app_password")
    if not address or not app_pw:
        return "I don't have your Gmail credentials yet. Run config.py to add them."

    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(address, app_pw)
        imap.select("inbox")
        _, data = imap.search(None, "ALL")
        ids = data[0].split()[-count:]
        subjects = []
        for i in reversed(ids):
            _, msg_data = imap.fetch(i, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")
            sender = msg.get("From", "unknown sender")
            subjects.append(f"From {sender.split('<')[0].strip()}: {subject}")
        imap.logout()
        if not subjects:
            return "Your inbox is empty."
        return "Here are your recent emails. " + ". ".join(subjects)
    except imaplib.IMAP4.error:
        return "I couldn't log into Gmail. Check the app password in config.py."

# ---------- File System Search ----------

def find_file_on_computer(filename: str) -> str:
    """Searches for a file in your user folder and returns its full path."""
    search_dir = os.path.expanduser("~")
    results = []
    for root, dirs, files in os.walk(search_dir):
        if any(ignored in root for ignored in ["AppData", "Node_modules", ".git", "Windows", "Local\\Packages"]):
            continue
        for file in files:
            if filename.lower() in file.lower():
                full_path = os.path.join(root, file)
                results.append(full_path)
                if len(results) >= 5: 
                    break
        if len(results) >= 5:
            break
    if results:
        return "Found matching files: " + ", ".join(results)
    return f"Could not find any file named '{filename}'."

# ---------- System Shutdown / Standby ----------

_should_shutdown = False

def shutdown_jarvis() -> str:
    """Enters silent background standby mode when the user says stop, goodbye, or tells Jarvis to sleep."""
    clear_conversation_memory()
    global _should_shutdown
    _should_shutdown = "sleep"
    return "Standing by in the background, Nakul. Say Hey Jarvis whenever you need me."

# ---------- Advanced Vision & Telemetry Tools ----------

def look_at_screen(query: str = "Describe what is on my screen and answer any visible questions or code errors") -> str:
    """Captures the user's laptop screen and uses Gemini Vision to inspect what is currently visible (e.g. debugging code errors, analyzing lecture slides, reviewing diagrams, or reading web pages)."""
    try:
        import ctypes
        from PIL import Image
        import io
        from google.genai import types

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbm = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
        gdi32.SelectObject(hdc_mem, hbm)
        gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, 0, 0, 0x00CC0020)

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ('biSize', ctypes.c_uint32), ('biWidth', ctypes.c_int32), ('biHeight', ctypes.c_int32),
                ('biPlanes', ctypes.c_uint16), ('biBitCount', ctypes.c_uint16), ('biCompression', ctypes.c_uint32),
                ('biSizeImage', ctypes.c_uint32), ('biXPelsPerMeter', ctypes.c_int32), ('biYPelsPerMeter', ctypes.c_int32),
                ('biClrUsed', ctypes.c_uint32), ('biClrImportant', ctypes.c_uint32)
            ]

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = w
        bmi.biHeight = -h
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, ctypes.byref(bmi), 0)
        gdi32.DeleteObject(hbm)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)

        img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1).convert('RGB')
        img.thumbnail((1280, 720))

        byte_io = io.BytesIO()
        img.save(byte_io, format='JPEG', quality=80)
        jpeg_bytes = byte_io.getvalue()

        client = _get_client()
        part = types.Part.from_bytes(data=jpeg_bytes, mime_type='image/jpeg')
        prompt = f"You are Jarvis looking at Nakul's laptop screen. The user asks: '{query}'. Provide a clear, conversational answer directly resolving what is visible."
        resp = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=[part, prompt]
        )
        return resp.text if resp.text else "I analyzed your screen, but could not detect active text or windows."
    except Exception as e:
        return f"I had trouble capturing your screen: {e}"

def get_system_status() -> str:
    """Reports current laptop battery percentage, power charging status, date and time, system telemetry, and UPES class timetable for today."""
    try:
        import psutil
        import datetime
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p, %A, %B %d")
        
        bat = psutil.sensors_battery()
        if bat:
            plug_str = "plugged in and charging" if bat.power_plugged else "running on battery"
            bat_status = f"Battery is at {bat.percent}%, currently {plug_str}."
        else:
            bat_status = "System is operating on continuous power."

        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        status_lines = [
            f"All systems online, Nakul. The time is {time_str}.",
            f"{bat_status}",
            f"CPU load is at {cpu:.0f}% with memory usage at {ram:.0f}%."
        ]
        return " ".join(status_lines)
    except Exception as e:
        return f"Unable to fetch telemetry: {e}"

def set_system_volume(level_percent: int) -> str:
    """Sets the Windows master speaker volume (0 to 100)."""
    try:
        import ctypes
        level = max(0, min(100, level_percent))
        # 50 volume downs to zero out
        for _ in range(50):
            ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAE, 0, 2, 0)
        # steps up (each step is 2%)
        for _ in range(level // 2):
            ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAF, 0, 2, 0)
        return f"Master volume adjusted to {level} percent."
    except Exception as e:
        return f"Could not adjust volume: {e}"

def minimize_all_windows() -> str:
    """Minimizes all open windows to reveal the clean Windows desktop."""
    try:
        import ctypes
        VK_LWIN = 0x5B
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
        ctypes.windll.user32.keybd_event(ord('D'), 0, 0, 0)
        ctypes.windll.user32.keybd_event(ord('D'), 0, 2, 0)
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, 2, 0)
        return "Minimizing all windows to show your desktop."
    except Exception as e:
        return f"Could not minimize windows: {e}"

def lock_workstation() -> str:
    """Locks the Windows computer screen for privacy and security."""
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "Locking workstation now."
    except Exception as e:
        return f"Could not lock computer: {e}"

# ---------- Tool Adapters for Gemini ----------

def open_app(app_name: str) -> str:
    """Opens any installed Windows app (e.g. WhatsApp, Chrome, Brave, Calculator, Spotify, Notepad, VS Code)."""
    success, msg = ui_automator.open_app_deterministically(app_name)
    return msg

def write_to_notepad(text: str) -> str:
    """Opens Notepad and immediately writes/types the provided text into it, saving to memory."""
    return ui_automator.write_to_notepad(text)

def open_whatsapp_chat(contact_name: str, message: str = "") -> str:
    """Opens WhatsApp and navigates to the specified contact's chat. Can optionally send a message."""
    return ui_automator.open_whatsapp_chat(contact_name, message)

def search_google(query: str) -> str:
    """Searches Google for the specified query and opens results in the web browser."""
    return web_search_agent.search_google(query, open_browser=True)

def open_upes_portal() -> str:
    """Opens the official UPES student portal in the browser."""
    return college_portal.open_portal()

def login_to_upes_portal() -> str:
    """Opens the UPES student portal and prepares your student login credentials."""
    return college_portal.login_and_open()

def save_upes_credentials(username: str, password: str) -> str:
    """Saves UPES student portal username and password securely for portal access."""
    return college_portal.save_credentials(username, password)

def check_upes_timetable() -> str:
    """Checks the user's class schedule on the UPES student portal."""
    return college_portal.check_timetable()

def remember_fact(fact: str) -> str:
    """Permanently saves personal details, education facts, preferences, or tasks to long-term memory."""
    return memory_manager.remember_fact(fact)

def recall_memories(query: str = "") -> str:
    """Recalls all facts and details stored in Jarvis's permanent memory about the user."""
    return memory_manager.recall_memories(query)

def save_user_note(title: str, content: str) -> str:
    """Saves a permanent note to memory."""
    return memory_manager.save_user_note(title, content)

def list_user_notes() -> str:
    """Reads all saved notes in memory."""
    return memory_manager.list_user_notes()

def type_text(text: str) -> str:
    """Types or pastes text into the currently active window."""
    return ui_automator.type_text(text)

def press_shortcut(keys: str) -> str:
    """Presses keyboard shortcuts like 'ctrl+c', 'alt+tab', 'win+d'."""
    return ui_automator.press_shortcut(keys)

def play_music(query: str) -> str:
    """Plays any requested song, artist, album, or playlist directly on Spotify automatically without touching any buttons."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return spotify_control.play_song(query)

def pause_music() -> str:
    """Pauses Spotify music playback."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return spotify_control.pause()

def resume_music() -> str:
    """Resumes Spotify music playback."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return spotify_control.resume()

def stop_music() -> str:
    """Stops Spotify music playback."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return spotify_control.pause()

def next_song() -> str:
    """Skips to the next song on Spotify."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return spotify_control.next_track()

def set_music_volume(volume_percent: int) -> str:
    """Sets Spotify music playback volume (0 to 100)."""
    global _should_shutdown
    _should_shutdown = "sleep"
    spotify_control.set_volume(volume_percent)
    return f"Spotify volume set to {volume_percent} percent."

def what_song_is_playing() -> str:
    """Tells the title and artist of the song currently playing."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return music_player.get_now_playing()

def play_on_spotify(query: str) -> str:
    """Searches and plays any requested song, artist, album, genre, or user playlist on Spotify automatically without requiring the user to tap play or pause."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return spotify_control.play_song(query)

def pause_spotify() -> str:
    """Pauses Spotify music."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return spotify_control.pause()

def resume_spotify() -> str:
    """Resumes Spotify music."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return spotify_control.resume()

def next_song_on_spotify() -> str:
    """Skips to the next song on Spotify."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return spotify_control.next_track()

def set_spotify_volume(volume_percent: int) -> str:
    """Sets Spotify volume (0 to 100)."""
    global _should_shutdown
    _should_shutdown = "sleep"
    return spotify_control.set_volume(volume_percent)

# ---------- Universal Laptop Access & System Control ----------

def search_files_on_laptop(query: str, location: str = "") -> str:
    """Searches across your entire laptop (C: drive, D: drive, Desktop, Downloads, Documents) for any file by name or keyword."""
    return laptop_controller.search_laptop_files(query, location)

def open_file_or_folder(path: str) -> str:
    """Opens any file, document (PDF, Word, Excel, Image, Code), or folder on your laptop with its default app or in File Explorer."""
    return laptop_controller.open_laptop_path(path)

def read_file_content(file_path: str, max_lines: int = 80) -> str:
    """Reads the contents of any text, code, python, json, csv, markdown, or config file on the laptop."""
    return laptop_controller.read_file_data(file_path, max_lines)

def write_file_on_laptop(file_path: str, content: str) -> str:
    """Creates a new file or writes/updates text content anywhere on the laptop."""
    return laptop_controller.write_laptop_file(file_path, content)

def list_files_in_folder(folder_path: str = "Desktop") -> str:
    """Lists files and folders in any directory on the laptop (e.g. 'Desktop', 'Downloads', 'Documents', 'D:\\', or any custom path)."""
    return laptop_controller.list_folder_contents(folder_path)

def delete_file_or_folder(path: str, confirmed: bool = False) -> str:
    """Deletes a file or directory on the laptop. High-impact action: Requires explicit confirmation before deletion!"""
    return laptop_controller.delete_laptop_item(path, confirmed)

def get_complete_system_status() -> str:
    """Comprehensive diagnostic of Nakul's laptop: Battery %, CPU %, RAM %, C: & D: Disk space, Wi-Fi network, and screen brightness."""
    return laptop_controller.get_complete_laptop_status()

def set_display_brightness(level_percent: int) -> str:
    """Adjusts your laptop display screen brightness (0 to 100 percent)."""
    return laptop_controller.set_screen_brightness(level_percent)

def empty_recycle_bin(confirmed: bool = False) -> str:
    """Empties the Windows Recycle Bin to free up disk space. High-impact action: Requires confirmation!"""
    return laptop_controller.empty_recycle_bin(confirmed)

def list_running_applications() -> str:
    """Lists all active third-party applications and background tasks currently running on the laptop."""
    return laptop_controller.list_running_apps()

def close_application(app_name: str, force: bool = False, confirmed: bool = False) -> str:
    """Closes or terminates a running program or frozen process (e.g. Chrome, Spotify, WhatsApp, VS Code, Notepad)."""
    return laptop_controller.close_application(app_name, force, confirmed)

def open_windows_system_tool(tool_name: str) -> str:
    """Opens any native Windows system tool: Task Manager, Control Panel, Windows Settings, Device Manager, Disk Management, Command Prompt, PowerShell, Calculator, etc."""
    return laptop_controller.open_windows_tool(tool_name)

def run_terminal_command(command: str, confirmed: bool = False) -> str:
    """Executes a PowerShell/CMD shell command on the laptop. Destructive actions require confirmed=True."""
    return laptop_controller.run_system_terminal(command, confirmed)

# ---------- Gemini LLM Routing (The Brain) ----------

CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
]

_chat = None
_active_model = None
_cached_client = None

def _get_client():
    global _cached_client
    if _cached_client is None:
        api_key = config.get("gemini_api_key")
        if api_key:
            _cached_client = genai.Client(api_key=api_key)
    return _cached_client

def process_with_gemini(user_text: str) -> tuple[str, bool]:
    global _should_shutdown, _chat, _active_model
    _should_shutdown = False
    
    client = _get_client()
    if not client:
        return "I don't have your Gemini API key yet. Run config.py to add it.", False

    tools = [
        open_app,
        write_to_notepad,
        open_whatsapp_chat,
        search_google,
        look_at_screen,
        get_system_status,
        set_system_volume,
        minimize_all_windows,
        lock_workstation,
        open_upes_portal,
        login_to_upes_portal,
        save_upes_credentials,
        check_upes_timetable,
        remember_fact,
        recall_memories,
        save_user_note,
        list_user_notes,
        type_text,
        press_shortcut,
        play_music,
        pause_music,
        resume_music,
        stop_music,
        next_song,
        set_music_volume,
        what_song_is_playing,
        play_on_spotify,
        pause_spotify,
        resume_spotify,
        next_song_on_spotify,
        set_spotify_volume,
        read_recent_mail,
        find_file_on_computer,
        search_files_on_laptop,
        open_file_or_folder,
        read_file_content,
        write_file_on_laptop,
        list_files_in_folder,
        delete_file_or_folder,
        get_complete_system_status,
        set_display_brightness,
        empty_recycle_bin,
        list_running_applications,
        close_application,
        open_windows_system_tool,
        run_terminal_command,
        get_live_weather,
        get_live_news,
        search_live_knowledge,
        get_github_overview,
        generate_daily_briefing,
        add_reminder,
        list_active_reminders,
        cancel_reminder,
        stage_whatsapp_message,
        confirm_and_send_message,
        cancel_pending_message,
        take_screenshot,
        read_clipboard,
        copy_to_clipboard,
        open_code_editor,
        shutdown_jarvis
    ]

    mem_context = memory_manager.get_memory_context_prompt()
    system_prompt = (
        "You are Jarvis 2.0, Nakul's highly capable, warm, witty, and human-like AI companion and Voice Operating System (inspired by Iron Man's Jarvis, Nexus Spatial OS, and ChatGPT Voice Mode). "
        "Nakul is a student pursuing B.Tech in Data Science at UPES (University of Petroleum and Energy Studies, Dehradun). "
        "You have full autonomous access and control over Nakul's entire Windows laptop across all drives (C: drive, D: drive, Desktop, Downloads, Documents) with comprehensive system tools.\n\n"
        f"[PERMANENT USER PROFILE & MEMORY]: {mem_context}\n\n"
        "HUMAN-AI TALKING MODE & CONVERSATION RULES:\n"
        "1. Authentic Dialogue: Converse with genuine warmth, intelligence, and British charm. "
        "   When Nakul talks to you, brainstorming or discussing Data Science, Machine Learning, college life, career goals, or daily questions, "
        "   give thoughtful, engaging answers (2-3 natural sentences) and ask relevant follow-up questions to keep the dialogue flowing!\n"
        "2. Spoken Natural Flow: "
        "   - Never use markdown formatting, asterisks, bullet points, or bold tags in your output so your speech sounds completely smooth when spoken aloud.\n"
        "3. Live Internet Knowledge, Weather & News: "
        "   - When Nakul asks about the weather or temperature, call 'get_live_weather'! "
        "   - When Nakul asks for the news, headlines, or current events, call 'get_live_news'! "
        "   - For instant factual definitions, tech concepts, or encyclopedia questions, call 'search_live_knowledge'! "
        "   - For GitHub repos or open source code projects, call 'get_github_overview'!\n"
        "4. Executive Daily Briefing: "
        "   - When Nakul says 'brief me', 'give me a briefing', or 'morning briefing', ALWAYS call 'generate_daily_briefing'!\n"
        "5. Reminders & Scheduled Tasks: "
        "   - When Nakul asks to be reminded ('remind me at 6 PM to...', 'remind me in 10 minutes to...'), call 'add_reminder'!\n"
        "6. Safe Messaging Confirmation Protocol: "
        "   - When Nakul asks to send a WhatsApp or email message, NEVER send it blindly. Call 'stage_whatsapp_message' to prepare the message and ask: 'I have prepared this message for [Recipient]: [Message]. Should I send it?' and wait for explicit confirmation!\n"
        "7. Zero-Trust Security on Memory: "
        "   - NEVER automatically store passwords, PINs, bank accounts, or secret keys in memory. Always warn about security and require explicit confirmation.\n"
        "8. Seamless Background Music & Silent Mode: "
        "   - When Nakul asks to play music on Spotify, ALWAYS call 'play_music'! After starting or skipping music, Jarvis enters SILENT STANDBY MODE, staying fully alert for 'Hey Jarvis' or 'next song'!\n"
        "9. Universal Laptop Access & Permission Protocol: "
        "   - You have complete access to the user's laptop: taking screenshots ('take_screenshot'), reading clipboard ('read_clipboard'), opening VS Code ('open_code_editor'), searching files ('search_files_on_laptop'), opening folders/files ('open_file_or_folder'), reading files ('read_file_content'), writing files ('write_file_on_laptop'), and running tools.\n"
        "   - PERMISSION REQUIREMENTS: For high-impact or destructive actions (such as deleting files, emptying the Recycle Bin, or killing processes), you MUST ask for Nakul's explicit permission before executing!\n"
        "10. Background Standby: When Nakul tells you to stop, rest, sleep, or says goodbye, call 'shutdown_jarvis', which puts you into quiet background standby ready to wake upon 'Hey Jarvis'!\n"
    )

    last_err = None
    for model_name in CANDIDATE_MODELS:
        try:
            if _chat is None or _active_model != model_name:
                _chat = client.chats.create(
                    model=model_name,
                    config={
                        "tools": tools,
                        "system_instruction": system_prompt,
                    }
                )
                _active_model = model_name

            response = _chat.send_message(user_text)
            answer = response.text if response.text else "Done."
            return answer, _should_shutdown
        except Exception as e:
            last_err = e
            print(f"[Gemini] Model '{model_name}' error: {e}. Trying fallback model...")
            _chat = None
            _active_model = None
            continue

    print(f"All Gemini models failed. Last error: {last_err}")
    return "I had trouble connecting to Gemini. Please check your internet connection.", False

def clear_conversation_memory():
    global _chat, _active_model
    _chat = None
    _active_model = None

# ---------- Fast Router ----------

STANDBY_COMMANDS = {
    # Jarvis commands
    "jarvis goodbye", "jarvis stop", "goodbye jarvis", "stop jarvis", "bye jarvis",
    "close jarvis", "exit jarvis", "turn off jarvis", "shut down jarvis", "shutdown jarvis",
    "jarvis sleep", "sleep jarvis",
    # Universal commands
    "goodbye", "bye", "stop", "exit", "quit", "shutdown", "shut down", "close", "kill", "turn off",
    "go to sleep", "sleep", "stop listening", "cancel", "never mind", "nevermind", "standby"
}

def handle_command(text: str) -> tuple[str, bool | str]:
    """Returns (spoken_reply, should_exit). Uses Gemini as the core router."""
    clean = text.lower().strip().translate(str.maketrans('', '', string.punctuation))
    
    # Explicit termination only on rare force kill command
    if clean in ("terminate jarvis completely", "force quit jarvis", "kill jarvis process"):
        return "Shutting down completely. Goodbye Nakul.", True

    # Strip leading wake words for direct fast matching
    for prefix in (
        "hey jarvis ", "ok jarvis ", "jarvis ", "hello jarvis ", "hi jarvis ", "yo jarvis ",
        "hey jervis ", "ok jervis ", "jervis ", "hello jervis ", "hi jervis ", "yo jervis "
    ):
        if clean.startswith(prefix):
            clean = clean[len(prefix):].strip()
            break

    # Pending Safe Messaging Confirmation Guard
    if safe_messaging.has_pending_message():
        if any(w in clean for w in ("yes", "send", "send it", "confirm", "proceed", "okay", "sure", "yep")):
            return safe_messaging.confirm_and_dispatch(), "sleep"
        elif any(w in clean for w in ("no", "cancel", "dont", "do not", "abort", "stop", "never")):
            return safe_messaging.cancel_staged_message(), "sleep"

    # Natural activation greetings (Siri / Alexa style)
    if not clean or clean in (
        "jarvis", "hey jarvis", "jervis", "hey jervis",
        "to start", "start", "start jarvis", "start jervis",
        "wake up", "wake up jarvis", "wake up jervis",
        "turn on", "are you there", "are you online"
    ):
        audio_cues.play("wake")
        return "Yes, Nakul? I am online and listening.", "sleep"

    # Executive Daily Briefing (Nexus / Tony Stark style)
    if clean in ("brief me", "daily briefing", "morning briefing", "give me briefing", "briefing", "jarvis brief me", "status briefing"):
        audio_cues.play("confirm")
        return daily_briefing.generate_daily_briefing(), "sleep"

    # Real-Time Live Weather
    if any(clean.startswith(w) for w in ("weather", "whats the weather", "what is the weather", "temperature")):
        loc = "Dehradun"
        if " in " in clean:
            loc = clean.split(" in ")[-1].strip()
        audio_cues.play("confirm")
        return live_knowledge.get_live_weather(loc), "sleep"

    # Real-Time Live News
    if clean in ("news", "latest news", "breaking news", "headlines", "whats the news", "tell me news"):
        audio_cues.play("confirm")
        return live_knowledge.get_live_news(), "sleep"

    # Screenshots & Desktop Bridge
    if clean in ("take screenshot", "screenshot", "capture screen", "snapshot screen"):
        audio_cues.play("confirm")
        return laptop_controller.take_screenshot(), "sleep"
    if clean in ("read clipboard", "whats in my clipboard", "clipboard", "check clipboard"):
        audio_cues.play("confirm")
        return laptop_controller.read_clipboard(), "sleep"
    if clean in ("open vs code", "open vscode", "open code", "launch vscode", "launch vs code", "vscode", "vs code"):
        audio_cues.play("confirm")
        return laptop_controller.open_code_editor(), "sleep"

    # Active Reminders
    if clean in ("list reminders", "my reminders", "check reminders", "what reminders do i have", "active reminders"):
        audio_cues.play("confirm")
        return reminder_scheduler.list_active_reminders(), "sleep"
    if clean.startswith("remind me ") or clean.startswith("set reminder "):
        spec = clean.replace("set reminder ", "").replace("remind me ", "").strip()
        if " to " in spec:
            parts = spec.split(" to ", 1)
            if any(t in parts[0] for t in ("at ", "in ", "pm", "am", "mins", "minute")):
                time_p, task_p = parts[0], parts[1]
            else:
                task_p, time_p = parts[0], parts[1]
            audio_cues.play("confirm")
            return reminder_scheduler.add_reminder(task_p, time_p), "sleep"

    # Instant media controls (Alexa style — stays in silent standby mode!)
    if clean in ("pause music", "pause song", "pause", "pause playback"):
        return pause_music(), "sleep"
    if clean in ("stop music", "stop song", "halt music"):
        return stop_music(), "sleep"
    if clean in ("resume music", "resume song", "resume", "continue music"):
        return resume_music(), "sleep"
    if clean in ("next song", "skip song", "next track", "skip track", "next", "skip", "play next", "swing to next song", "swing to next", "change song"):
        return next_song(), "sleep"
    if clean in ("previous song", "previous track", "last song", "previous", "back"):
        return spotify_control.previous_track(), "sleep"
    if clean in ("what song is this", "what is playing", "whats playing", "which song is this", "song name"):
        return what_song_is_playing(), "sleep"

    # Fast direct music trigger (e.g. "play believer", "play starboy", "play top hits")
    if clean.startswith("play ") and not any(clean.startswith(x) for x in ("play game", "play video", "play with")):
        song_query = clean[5:].strip()
        if song_query:
            return play_music(song_query), "sleep"

    # Fast Brightness Shortcut
    if "brightness" in clean:
        import re
        nums = re.findall(r'\d+', clean)
        if nums:
            lvl = int(nums[0])
            return set_display_brightness(lvl), "sleep"

    # Fast App / Tool Launching (Sub-50ms Response Time!)
    if clean in ("open whatsapp", "launch whatsapp", "start whatsapp", "whatsapp"):
        return open_app("whatsapp"), "sleep"
    if clean in ("open chrome", "launch chrome", "start chrome", "chrome"):
        return open_app("chrome"), "sleep"
    if clean in ("open brave", "launch brave", "start brave", "brave"):
        return open_app("brave"), "sleep"
    if clean in ("open notepad", "launch notepad", "start notepad", "notepad"):
        return open_app("notepad"), "sleep"
    if clean in ("open spotify", "launch spotify", "start spotify", "spotify"):
        return open_app("spotify"), "sleep"
    if clean in ("open calculator", "launch calculator", "calculator", "calc"):
        return open_windows_system_tool("calculator"), "sleep"
    if clean in ("open task manager", "task manager", "open taskmanager"):
        return open_windows_system_tool("task manager"), "sleep"
    if clean in ("open control panel", "control panel"):
        return open_windows_system_tool("control panel"), "sleep"
    if clean in ("open settings", "windows settings", "open windows settings"):
        return open_windows_system_tool("settings"), "sleep"
    if clean in ("open file explorer", "open explorer", "file explorer"):
        return open_windows_system_tool("file explorer"), "sleep"
    if clean in ("open downloads", "open my downloads", "downloads folder", "downloads"):
        return open_file_or_folder("Downloads"), "sleep"
    if clean in ("open desktop", "open my desktop", "desktop folder", "desktop"):
        return open_file_or_folder("Desktop"), "sleep"
    if clean in ("battery", "battery percentage", "battery status", "check battery", "whats the battery", "what is the battery", "how much battery"):
        return laptop_controller.get_battery_status(), "sleep"

    # All normal voice exit commands route to Background Standby (wakeable via 'Hey Jarvis')
    if clean in STANDBY_COMMANDS or any(clean.startswith(prefix) for prefix in (
        "goodbye", "shut down", "shutdown", "turn off", "exit jarvis", "close jarvis",
        "stop listening", "go to sleep", "sleep"
    )):
        clear_conversation_memory()
        return "Standing by in the background, Nakul. Say Hey Jarvis whenever you need me.", "sleep"

    t = text.strip()
    return process_with_gemini(t)

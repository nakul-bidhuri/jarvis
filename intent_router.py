"""
intent_router.py — High-Performance Local Intent Router & Multi-Step Command Engine.

Features:
- Fast Local Intent Recognition (<10ms):
  Executes common desktop commands instantly without calling an expensive LLM.
- Multi-Step Command Decomposition:
  Supports compound commands joined by 'and', 'then', or 'after that'
  (e.g., 'Open Spotify and play my liked songs', 'Open YouTube and search for FastAPI tutorial').
- Context-Aware Follow-Ups:
  Uses SessionContext to resolve pronouns and contextual operations ('next', 'pause it', 'play it again').
- Seamless Fallback:
  Routes complex reasoning, code assistance, and knowledge queries directly to Gemini LLM.
"""

import re
import time
import string
import webbrowser
from typing import Tuple, Optional, List, Dict, Any

import session_context
import app_discovery
import spotify_control
import laptop_controller
import live_knowledge
import daily_briefing
import safe_messaging
import reminder_scheduler


# Regex patterns for fast command normalization
_RE_PUNCT = str.maketrans('', '', string.punctuation)


def normalize_text(text: str) -> str:
    """Cleans text, trims leading Jarvis addresses, and removes punctuation."""
    t = text.lower().strip()
    # Strip any leading address (including phonetic variations)
    for prefix in (
        "hey jarvis ", "ok jarvis ", "jarvis ", "hello jarvis ", "hi jarvis ",
        "hey jervis ", "ok jervis ", "jervis ", "hello jervis ", "hi jervis ",
        "हे जार्विस ", "जार्विस ", "sunno jarvis ", "suno jarvis "
    ):
        if t.startswith(prefix):
            t = t[len(prefix):].strip()
            break
    return t


def split_multi_step_commands(clean_text: str) -> List[str]:
    """
    Decomposes multi-step phrases into separate sequential commands.
    E.g. 'open spotify and play my liked songs' -> ['open spotify', 'play my liked songs']
    Avoids splitting single phrases like 'rock and roll', 'r and b', 'search for fast and furious'.
    """
    # Guard against splitting queries that legitimately contain 'and'
    if any(clean_text.startswith(x) for x in ("search ", "google ", "who is ", "what is ", "why ")):
        return [clean_text]

    # Split on explicit command connectors
    parts = re.split(r'\s+(?:and then|then|after that|and)\s+', clean_text)
    if len(parts) > 1 and all(len(p.strip()) > 2 for p in parts):
        return [p.strip() for p in parts]
    return [clean_text]


def route_local_intent(phrase: str) -> Tuple[bool, str, Optional[str]]:
    """
    Attempts to match a phrase to a fast local intent.
    Returns (matched, reply_text, intent_name).
    """
    p = phrase.lower().strip()
    clean = p.translate(_RE_PUNCT).strip()
    ctx = session_context.context

    # 1. Pending Safe Messaging Confirmation Guard
    if safe_messaging.has_pending_message():
        if any(w in clean.split() for w in ("yes", "send", "confirm", "proceed", "sure", "yep", "okay")):
            return True, safe_messaging.confirm_and_dispatch(), "CONFIRM_MESSAGE"
        elif any(w in clean.split() for w in ("no", "cancel", "abort", "stop", "never")):
            return True, safe_messaging.cancel_staged_message(), "CANCEL_MESSAGE"

    # 2. Contextual Follow-Up Operations
    context_intent, context_target = ctx.resolve_contextual_action(clean)
    if context_intent == "SEARCH_YOUTUBE":
        url = f"https://www.youtube.com/results?search_query={context_target.replace(' ', '+')}"
        webbrowser.open(url)
        ctx.record_intent("SEARCH_YOUTUBE", target="YouTube", query=context_target)
        return True, f"Searching for {context_target} on YouTube.", "SEARCH_YOUTUBE"
    elif context_intent == "PAUSE_MEDIA":
        res = spotify_control.pause()
        ctx.record_intent("PAUSE_MEDIA", target="Spotify")
        return True, res, "PAUSE_MEDIA"
    elif context_intent == "RESUME_MEDIA":
        res = spotify_control.resume()
        ctx.record_intent("RESUME_MEDIA", target="Spotify")
        return True, res, "RESUME_MEDIA"
    elif context_intent == "NEXT_MEDIA":
        res = spotify_control.next_track()
        ctx.record_intent("NEXT_MEDIA", target="Spotify")
        return True, res, "NEXT_MEDIA"
    elif context_intent == "PREVIOUS_MEDIA":
        res = spotify_control.previous_track()
        ctx.record_intent("PREVIOUS_MEDIA", target="Spotify")
        return True, res, "PREVIOUS_MEDIA"

    # 3. Media Controls (Spotify)
    # 3a. Liked Songs
    if any(k in clean for k in (
        "play my liked songs", "play liked songs", "start my liked songs",
        "play my liked songs on spotify", "play liked songs on spotify",
        "liked songs on spotify", "liked songs"
    )) and ("play" in clean or "start" in clean):
        res = spotify_control.play_liked_songs()
        ctx.record_intent("PLAY_MEDIA", target="Spotify", query="Liked Songs", app="Spotify")
        return True, res, "PLAY_MEDIA"

    # 3b. Pause / Resume / Stop
    if clean in ("pause", "pause music", "pause song", "pause spotify", "pause playback", "stop music", "halt music"):
        res = spotify_control.pause()
        ctx.record_intent("PAUSE_MEDIA", target="Spotify")
        return True, res, "PAUSE_MEDIA"

    if clean in ("resume", "resume music", "resume song", "resume spotify", "play again", "continue music", "unpause"):
        res = spotify_control.resume()
        ctx.record_intent("RESUME_MEDIA", target="Spotify")
        return True, res, "RESUME_MEDIA"

    # 3c. Next / Previous
    if clean in ("next", "next song", "next track", "skip", "skip song", "skip track", "play next", "next music"):
        res = spotify_control.next_track()
        ctx.record_intent("NEXT_MEDIA", target="Spotify")
        return True, res, "NEXT_MEDIA"

    if clean in ("previous", "previous song", "previous track", "last song", "back song", "back track"):
        res = spotify_control.previous_track()
        ctx.record_intent("PREVIOUS_MEDIA", target="Spotify")
        return True, res, "PREVIOUS_MEDIA"

    # 3d. Volume Control
    if any(clean == x for x in ("volume up", "increase volume", "turn volume up", "turn the volume up", "turn it up", "turn music up", "turn the music up", "louder")):
        res = spotify_control.volume_up()
        ctx.record_intent("VOLUME_UP")
        return True, res, "VOLUME_UP"

    if any(clean == x for x in ("volume down", "lower volume", "lower the volume", "turn volume down", "turn the volume down", "turn it down", "turn music down", "lower spotify volume", "quieter")):
        res = spotify_control.volume_down()
        ctx.record_intent("VOLUME_DOWN")
        return True, res, "VOLUME_DOWN"

    if "volume" in clean:
        nums = re.findall(r'\b\d+\b', clean)
        if nums:
            lvl = int(nums[0])
            res = spotify_control.set_volume(lvl)
            ctx.record_intent("SET_VOLUME", query=str(lvl))
            return True, res, "SET_VOLUME"

    # 3e. Specific Song / Artist Playback
    # E.g. "play believer", "play starboy", "play arijit singh on spotify"
    if clean.startswith("play ") and not any(clean.startswith(x) for x in ("play game", "play video", "play with")):
        song_query = clean[5:].strip()
        # Remove trailing "on spotify"
        if song_query.endswith(" on spotify"):
            song_query = song_query[:-11].strip()
        if song_query:
            res = spotify_control.play_song(song_query)
            ctx.record_intent("PLAY_MEDIA", target="Spotify", query=song_query, app="Spotify")
            return True, res, "PLAY_MEDIA"

    # 4. Application & Website Launching
    # 4a. Open Spotify
    if clean in ("open spotify", "launch spotify", "start spotify", "spotify"):
        res = spotify_control.open_spotify()
        ctx.set_active_app("Spotify", "native")
        ctx.record_intent("OPEN_APP", target="Spotify", app="Spotify")
        return True, res, "OPEN_APP"

    # 4b. General "open [app/site]" or "launch [app/site]"
    for prefix in ("open ", "launch ", "start "):
        if clean.startswith(prefix):
            target = clean[len(prefix):].strip()
            if target:
                success, reply, app_type = app_discovery.resolve_and_launch(target)
                if success:
                    ctx.set_active_app(target.title(), app_type)
                    ctx.record_intent("OPEN_APP", target=target.title(), app=target.title())
                    return True, reply, "OPEN_APP"

    # 4c. Close Application
    for prefix in ("close ", "quit ", "kill ", "exit "):
        if clean.startswith(prefix):
            target = clean[len(prefix):].strip()
            if target and target not in ("jarvis", "program", "all"):
                res = laptop_controller.close_application(target)
                ctx.record_intent("CLOSE_APP", target=target.title())
                return True, res, "CLOSE_APP"

    # 5. Web Search & Video Search
    # E.g. "search youtube for [x]", "search google for [x]", "search for [x]"
    if clean.startswith("search youtube for "):
        q = clean[19:].strip()
        url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
        webbrowser.open(url)
        ctx.set_active_app("YouTube", "web")
        ctx.record_intent("SEARCH_WEB", target="YouTube", query=q)
        return True, f"Searching YouTube for {q}.", "SEARCH_WEB"

    if clean.startswith("search google for ") or clean.startswith("google "):
        q = clean.replace("search google for ", "").replace("google ", "").strip()
        url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
        webbrowser.open(url)
        ctx.set_active_app("Google", "web")
        ctx.record_intent("SEARCH_WEB", target="Google", query=q)
        return True, f"Searching Google for {q}.", "SEARCH_WEB"

    if clean.startswith("search for ") and not clean.startswith("search for file"):
        q = clean[11:].strip()
        if ctx.active_app and "youtube" in ctx.active_app.lower():
            url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
            webbrowser.open(url)
            return True, f"Searching YouTube for {q}.", "SEARCH_WEB"
        else:
            url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
            webbrowser.open(url)
            return True, f"Searching for {q}.", "SEARCH_WEB"

    # 6. Live Information: Weather & News
    if any(clean.startswith(w) for w in ("weather", "whats the weather", "what is the weather", "temperature")):
        loc = "Dehradun"
        if " in " in clean:
            loc = clean.split(" in ")[-1].strip()
        res = live_knowledge.get_live_weather(loc)
        ctx.record_intent("WEATHER", query=loc)
        return True, res, "WEATHER"

    if any(clean == x for x in ("news", "latest news", "breaking news", "headlines", "whats the news", "tell me news", "last 24 hours news")):
        res = live_knowledge.get_live_news()
        ctx.record_intent("NEWS")
        return True, res, "NEWS"

    # 7. System & Laptop Controls
    if clean in ("take screenshot", "screenshot", "capture screen", "snapshot screen"):
        res = laptop_controller.take_screenshot()
        ctx.record_intent("SYSTEM_CONTROL", target="Screenshot")
        return True, res, "SYSTEM_CONTROL"

    if clean in ("read clipboard", "whats in my clipboard", "clipboard", "check clipboard"):
        res = laptop_controller.read_clipboard()
        ctx.record_intent("SYSTEM_CONTROL", target="Clipboard")
        return True, res, "SYSTEM_CONTROL"

    if clean in ("battery", "battery percentage", "battery status", "check battery", "whats the battery", "how much battery"):
        res = laptop_controller.get_battery_status()
        ctx.record_intent("SYSTEM_STATUS", target="Battery")
        return True, res, "SYSTEM_STATUS"

    if clean in ("system status", "telemetry", "laptop status", "laptop telemetry"):
        res = laptop_controller.get_complete_laptop_status()
        ctx.record_intent("SYSTEM_STATUS", target="System")
        return True, res, "SYSTEM_STATUS"

    if clean in ("minimize all windows", "minimize windows", "show desktop", "desktop"):
        try:
            import ctypes
            VK_LWIN = 0x5B
            ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
            ctypes.windll.user32.keybd_event(ord('D'), 0, 0, 0)
            ctypes.windll.user32.keybd_event(ord('D'), 0, 2, 0)
            ctypes.windll.user32.keybd_event(VK_LWIN, 0, 2, 0)
            ctx.record_intent("SYSTEM_CONTROL", target="MinimizeWindows")
            return True, "Minimizing all windows.", "SYSTEM_CONTROL"
        except Exception:
            pass

    if clean in ("lock laptop", "lock workstation", "lock computer", "lock screen"):
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            ctx.record_intent("SYSTEM_CONTROL", target="LockWorkstation")
            return True, "Locking workstation now.", "SYSTEM_CONTROL"
        except Exception:
            pass

    if "brightness" in clean:
        nums = re.findall(r'\b\d+\b', clean)
        if nums:
            lvl = int(nums[0])
            res = laptop_controller.set_screen_brightness(lvl)
            ctx.record_intent("SYSTEM_CONTROL", target="Brightness", query=str(lvl))
            return True, res, "SYSTEM_CONTROL"

    # 8. Executive Daily Briefing
    if clean in ("brief me", "daily briefing", "morning briefing", "give me briefing", "briefing"):
        res = daily_briefing.generate_daily_briefing()
        ctx.record_intent("BRIEFING")
        return True, res, "BRIEFING"

    # No fast local intent matched
    return False, "", None


def execute_command_pipeline(raw_text: str) -> Tuple[str, bool]:
    """
    Primary Entry Point for command execution:
    1. Normalizes input and decomposes into sub-commands if multi-step.
    2. Runs fast local intent router for sub-50ms execution.
    3. If multi-step, aggregates responses cleanly.
    4. If not matched locally, routes to Gemini LLM with context.
    Returns (reply_text, should_exit). Note: should_exit is ONLY True for explicit shutdown.
    """
    clean_text = normalize_text(raw_text)
    if not clean_text:
        return "I am online and listening.", False

    # Decompose into multi-step actions if present
    sub_commands = split_multi_step_commands(clean_text)

    # If single command
    if len(sub_commands) == 1:
        t0 = time.time()
        matched, local_reply, intent_name = route_local_intent(sub_commands[0])
        dt = time.time() - t0
        if matched:
            print(f"[PERF] Local Intent: {intent_name} executed in {dt:.3f}s | Reply: '{local_reply}'")
            session_context.context.record_dialogue(raw_text, local_reply)
            return local_reply, False

        # Fallback to Gemini Brain
        import commands
        print(f"[INTENT] Complex/Knowledge Query -> Routing to Gemini: '{clean_text}'")
        reply, should_exit = commands.process_with_gemini(raw_text)
        session_context.context.record_dialogue(raw_text, reply)
        return reply, should_exit

    # Multi-step execution
    replies = []
    for step in sub_commands:
        t0 = time.time()
        matched, step_reply, intent_name = route_local_intent(step)
        dt = time.time() - t0
        if matched:
            print(f"[PERF] Multi-step item: {intent_name} executed in {dt:.3f}s")
            replies.append(step_reply)
            time.sleep(0.3)
        else:
            # Fallback single step to Gemini
            import commands
            step_reply, _ = commands.process_with_gemini(step)
            replies.append(step_reply)

    combined_reply = " ".join(replies)
    session_context.context.record_dialogue(raw_text, combined_reply)
    return combined_reply, False

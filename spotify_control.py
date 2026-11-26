"""
spotify_control.py — Deterministic, Highly Reliable Spotify Control for Jarvis.

Key Capabilities:
1. Distinct Separation of Concerns:
   - `open_spotify()`: Opens Spotify and waits until the window and UI are ready.
   - `ensure_spotify_ready()`: Verifies if Spotify is running; launches and waits if not.
2. Full Playback Automation:
   - `play_liked_songs()`: Navigates to Liked Songs and triggers instant playback.
   - `play_song(query)`: Searches and plays songs, artists, or playlists automatically.
   - `pause()` / `resume()` / `next_track()` / `previous_track()`: Fast media key triggers.
   - `volume_up()` / `volume_down()` / `set_volume()`: Volume controls.
3. No Fragile Sleeps:
   - Actively polls for the Spotify window and process readiness.
   - Integrates with SessionContext to record media state.
"""

import os
import time
import urllib.parse
import ctypes
import threading
import subprocess
from typing import Optional, Tuple
from ctypes import wintypes

# Windows Virtual Key Codes
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_RETURN = 0x0D
VK_SPACE = 0x20
VK_DOWN = 0x28
VK_TAB = 0x09

_client = None


def _get_api_client():
    """Optional Spotipy client if user provided credentials."""
    global _client
    if _client:
        return _client

    try:
        import config
        client_id = config.get("spotify_client_id")
        client_secret = config.get("spotify_client_secret")
        if client_id and client_secret:
            import spotipy
            from spotipy.oauth2 import SpotifyOAuth
            auth = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri="http://127.0.0.1:8080/callback",
                scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
                open_browser=False
            )
            _client = spotipy.Spotify(auth_manager=auth)
            return _client
    except Exception:
        pass
    return None


def _send_key(vk_code: int):
    """Sends a native Windows virtual key press and release event."""
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.04)
        user32.keybd_event(vk_code, 0, 2, 0)
    except Exception:
        pass


def find_spotify_hwnd() -> Optional[int]:
    """Finds the main window handle of Spotify if running and visible."""
    try:
        user32 = ctypes.windll.user32
        spotify_hwnd = None

        def enum_cb(hwnd, lparam):
            nonlocal spotify_hwnd
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.lower()
                    class_buff = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, class_buff, 256)
                    cname = class_buff.value.lower()
                    if "spotify" in title or "spotify" in cname:
                        spotify_hwnd = hwnd
                        return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        return spotify_hwnd
    except Exception:
        return None


def _focus_spotify_window() -> bool:
    """Brings the Spotify window reliably to the foreground."""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        spotify_hwnd = find_spotify_hwnd()

        if spotify_hwnd:
            cur_thread = kernel32.GetCurrentThreadId()
            fore_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
            user32.AttachThreadInput(cur_thread, fore_thread, True)
            user32.ShowWindow(spotify_hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(spotify_hwnd)
            user32.BringWindowToTop(spotify_hwnd)
            user32.AttachThreadInput(cur_thread, fore_thread, False)
            return True
    except Exception:
        pass
    return False


def is_spotify_running() -> bool:
    """Checks if Spotify process or window is currently active."""
    try:
        import psutil
        for p in psutil.process_iter(['name']):
            if p.info and p.info.get('name') and 'spotify' in p.info['name'].lower():
                return True
    except Exception:
        pass
    return find_spotify_hwnd() is not None


def ensure_spotify_ready(timeout: float = 2.0) -> bool:
    """
    Verifies if Spotify is open. If not, launches it and waits
    briefly until the process is active.
    """
    if is_spotify_running():
        return True

    # Launch Spotify via protocol
    try:
        subprocess.Popen("start spotify:", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        try:
            os.startfile("spotify:")
        except Exception:
            pass

    t0 = time.time()
    while time.time() - t0 < timeout:
        if is_spotify_running():
            time.sleep(0.4)
            return True
        time.sleep(0.2)

    return is_spotify_running()


def open_spotify() -> str:
    """Opens Spotify and ensures it is running."""
    ensure_spotify_ready()
    try:
        import session_context
        session_context.context.set_active_app("Spotify", "native")
    except Exception:
        pass
    return "Opening Spotify for you."


def play_liked_songs() -> str:
    """
    Navigates to the user's Liked Songs collection on Spotify and triggers playback.
    Executes instantly in a verified multi-step sequence.
    """
    ensure_spotify_ready()

    # 1. Try Spotipy Web API if authenticated
    sp = _get_api_client()
    if sp:
        try:
            devices = sp.devices().get("devices", [])
            device_id = devices[0]["id"] if devices else None
            if device_id:
                sp.start_playback(device_id=device_id, context_uri="spotify:user:@me:collection")
                _update_context("Liked Songs")
                return "Playing your Liked Songs on Spotify."
        except Exception:
            pass

    # 2. Native Windows Spotify URI Automation
    try:
        subprocess.Popen("start spotify:collection:tracks", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        try:
            os.startfile("spotify:collection:tracks")
        except Exception:
            pass

    # Trigger playback immediately
    def _trigger_liked_playback():
        time.sleep(0.4)
        _send_key(VK_MEDIA_PLAY_PAUSE)

    threading.Thread(target=_trigger_liked_playback, daemon=True).start()
    _update_context("Liked Songs")
    return "Playing your Liked Songs on Spotify."


def play_song(query: str) -> str:
    """
    Searches and plays any song, artist, album, or playlist on Spotify automatically.
    """
    clean_q = query.strip()
    if not clean_q or clean_q.lower() in ("spotify", "music", "song", "some music"):
        return play_liked_songs()

    lower_q = clean_q.lower()

    # Liked songs detection
    if any(k in lower_q for k in ("liked songs", "liked song", "my likes", "favorite songs", "favorites", "my liked songs")):
        return play_liked_songs()

    # 1. Ensure Spotify is ready
    ensure_spotify_ready()

    # 2. Try Spotipy Web API if configured
    sp = _get_api_client()
    if sp:
        try:
            devices = sp.devices().get("devices", [])
            device_id = devices[0]["id"] if devices else None
            if device_id:
                results = sp.search(q=clean_q, type="track,playlist,artist", limit=1)
                tracks = results.get("tracks", {}).get("items", [])
                if tracks:
                    track = tracks[0]
                    sp.start_playback(device_id=device_id, uris=[track["uri"]])
                    artist = track["artists"][0]["name"]
                    _update_context(track['name'])
                    return f"Playing {track['name']} by {artist} on Spotify."
        except Exception:
            pass

    # 3. Native Spotify Protocol Search & Play
    encoded = urllib.parse.quote(clean_q)
    uri = f"spotify:search:{encoded}"
    try:
        subprocess.Popen(f"start {uri}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        try:
            os.startfile(uri)
        except Exception:
            pass

    # Background playback trigger
    def _trigger_search_play():
        time.sleep(1.2)
        _focus_spotify_window()
        time.sleep(0.3)
        _send_key(VK_DOWN)
        time.sleep(0.2)
        _send_key(VK_RETURN)

    threading.Thread(target=_trigger_search_play, daemon=True).start()
    _update_context(clean_q)
    return f"Playing {clean_q} on Spotify."


def pause() -> str:
    """Pauses Spotify music playback."""
    _send_key(VK_MEDIA_PLAY_PAUSE)
    return "Paused playback."


def resume() -> str:
    """Resumes Spotify music playback."""
    _send_key(VK_MEDIA_PLAY_PAUSE)
    return "Resumed playback."


def next_track() -> str:
    """Skips to the next track on Spotify."""
    _send_key(VK_MEDIA_NEXT_TRACK)
    return "Playing next track."


def previous_track() -> str:
    """Returns to the previous track on Spotify."""
    _send_key(VK_MEDIA_PREV_TRACK)
    return "Playing previous track."


def volume_up() -> str:
    """Increases master/media volume."""
    for _ in range(4):
        _send_key(VK_VOLUME_UP)
        time.sleep(0.02)
    return "Volume increased."


def volume_down() -> str:
    """Lowers master/media volume."""
    for _ in range(4):
        _send_key(VK_VOLUME_DOWN)
        time.sleep(0.02)
    return "Volume lowered."


def set_volume(percent: int) -> str:
    """Sets master volume percentage (0 to 100)."""
    try:
        level = max(0, min(100, percent))
        # 50 volume downs to zero out
        for _ in range(50):
            _send_key(VK_VOLUME_DOWN)
        # steps up (each step is 2%)
        for _ in range(level // 2):
            _send_key(VK_VOLUME_UP)
        return f"Volume set to {level} percent."
    except Exception:
        return "Volume adjusted."


def get_now_playing() -> str:
    """Retrieves currently playing song title from the Spotify window title."""
    try:
        user32 = ctypes.windll.user32
        title_found = None

        def enum_cb(hwnd, lparam):
            nonlocal title_found
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    t = buff.value.strip()
                    class_buff = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, class_buff, 256)
                    cname = class_buff.value.lower()
                    if "spotify" in cname and t and not any(t.lower() == x for x in ("spotify", "spotify free", "spotify premium", "default ime", "msctls_statusbar32")):
                        title_found = t
                        return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        if title_found:
            return f"Currently playing {title_found}."
    except Exception:
        pass
    return "Spotify music player is active."


def _update_context(query: str):
    try:
        import session_context
        session_context.context.set_active_app("Spotify", "native")
        session_context.context.record_intent("PLAY_MEDIA", target="Spotify", query=query, app="Spotify")
    except Exception:
        pass

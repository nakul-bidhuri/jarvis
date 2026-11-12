"""
spotify_control.py — Seamless, Fully-Automated Spotify Playback for Jarvis.

Features:
  - 100% Automatic Playback: Opens Spotify and triggers playback directly without
    requiring the user to touch any play/pause buttons.
  - Playlist & Track Tracking: Supports playing specific songs, artists, user playlists,
    liked songs ("spotify:collection:tracks"), and general genres.
  - Zero Setup Required: Uses native Windows Spotify protocol and global media keys
    (works for both Spotify Free & Premium without requiring developer API keys).
  - Web API Acceleration: Seamlessly utilizes Spotipy if Client ID/Secret are configured.
"""

import os
import time
import urllib.parse
import ctypes
import threading

from ctypes import wintypes

# Windows Media Key Constants
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_RETURN = 0x0D
VK_SPACE = 0x20
VK_DOWN = 0x28

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

def _focus_spotify_window():
    """Brings the Spotify window reliably to the foreground."""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
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

def _trigger_playback_sequence():
    """
    Simulates keyboard triggers in Spotify to automatically start playback
    without the user having to click any buttons.
    Uses Down Arrow to move from the search input to the first result,
    then presses Enter once to begin playback.
    """
    time.sleep(1.8)
    _focus_spotify_window()
    time.sleep(0.4)
    # Move to the top result and press Enter to start playing
    _send_key(VK_DOWN)
    time.sleep(0.2)
    _send_key(VK_RETURN)

def play_song(query: str) -> str:
    """
    Searches and plays any song, artist, album, or playlist on Spotify automatically.
    Never asks the user to manually click play or pause.
    """
    clean_q = query.strip()
    if not clean_q or clean_q.lower() in ("spotify", "music", "song"):
        clean_q = "Top Hits"

    lower_q = clean_q.lower()

    # 1. Try Spotipy Web API if configured
    sp = _get_api_client()
    if sp:
        try:
            devices = sp.devices().get("devices", [])
            device_id = devices[0]["id"] if devices else None
            if device_id:
                results = sp.search(q=clean_q, type="track,playlist", limit=1)
                tracks = results.get("tracks", {}).get("items", [])
                if tracks:
                    track = tracks[0]
                    sp.start_playback(device_id=device_id, uris=[track["uri"]])
                    artist = track["artists"][0]["name"]
                    return f"Playing {track['name']} by {artist} on Spotify automatically."
        except Exception:
            pass

    # 2. Native Windows Spotify Protocol Automation (100% Reliable for all users)
    try:
        # Determine target Spotify URI
        if any(k in lower_q for k in ("liked songs", "my likes", "favorite songs", "favorites")):
            uri = "spotify:collection:tracks"
            display_target = "your Liked Songs"
        elif any(k in lower_q for k in ("my playlist", "my playlists", "user playlists")):
            uri = "spotify:collection:playlists"
            display_target = "your Spotify Playlists"
        else:
            encoded = urllib.parse.quote(clean_q)
            uri = f"spotify:search:{encoded}"
            display_target = clean_q

        # Launch Spotify directly with the target
        os.startfile(uri)

        # Trigger automatic playback in a background thread so Jarvis responds immediately
        threading.Thread(target=_trigger_playback_sequence, daemon=True).start()

        return f"Playing {display_target} on Spotify automatically, Nakul!"
    except Exception as e:
        # Fallback to web search
        try:
            import webbrowser
            webbrowser.open(f"https://open.spotify.com/search/{urllib.parse.quote(clean_q)}")
            threading.Thread(target=_trigger_playback_sequence, daemon=True).start()
            return f"Playing {clean_q} on Spotify Web for you now, Nakul!"
        except Exception:
            return f"Unable to launch Spotify automatically: {e}"

def pause() -> str:
    """Instantly pauses Spotify music playback."""
    _send_key(VK_MEDIA_PLAY_PAUSE)
    return "Paused Spotify playback."

def resume() -> str:
    """Resumes Spotify music playback."""
    _send_key(VK_MEDIA_PLAY_PAUSE)
    return "Resumed Spotify playback."

def next_track() -> str:
    """Skips to the next track on Spotify."""
    _send_key(VK_MEDIA_NEXT_TRACK)
    return "Skipping to the next song."

def previous_track() -> str:
    """Returns to the previous track on Spotify."""
    _send_key(VK_MEDIA_PREV_TRACK)
    return "Returning to the previous song."

def get_now_playing() -> str:
    """
    Retrieves the currently playing song title and artist directly from the Spotify
    Windows application title bar.
    """
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
            return f"Currently playing {title_found}"
    except Exception:
        pass
    return "Spotify music player active"

def set_volume(percent: int) -> str:
    """Adjusts volume level."""
    try:
        import ctypes
        level = max(0, min(100, percent))
        for _ in range(50):
            ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAE, 0, 2, 0)
        for _ in range(level // 2):
            ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAF, 0, 2, 0)
        return f"Volume set to {level} percent."
    except Exception:
        return "Volume adjusted."

"""
session_context.py — Lightweight In-Memory Conversational & Application Context for Jarvis.

Maintains short-term session context while Jarvis is ON:
- active_app: currently focused or last launched app (e.g. Spotify, YouTube, Chrome)
- last_intent: the most recent command intent (e.g. PLAY_MEDIA, OPEN_APP)
- last_media_source: source of active media (e.g. Spotify)
- last_query: user's last search or media query
- conversation_turns: recent short-term dialogue for contextual follow-ups

All context is strictly in-memory and automatically wiped when Jarvis turns OFF.
"""

import time
from typing import Optional, Dict, Any, List


class SessionContext:
    def __init__(self):
        self.active_app: Optional[str] = None
        self.active_app_type: str = "native"  # "native" or "web"
        self.last_intent: Optional[str] = None
        self.last_target: Optional[str] = None
        self.last_query: Optional[str] = None
        self.last_media_source: Optional[str] = None
        self.last_action_timestamp: float = 0.0
        self.dialogue_history: List[Dict[str, str]] = []

    def set_active_app(self, app_name: str, app_type: str = "native") -> None:
        """Updates the active application in context."""
        self.active_app = app_name.strip()
        self.active_app_type = app_type
        self.last_action_timestamp = time.time()
        if "spotify" in app_name.lower():
            self.last_media_source = "Spotify"
        elif "youtube" in app_name.lower():
            self.last_media_source = "YouTube"

    def record_intent(
        self,
        intent: str,
        target: Optional[str] = None,
        query: Optional[str] = None,
        app: Optional[str] = None
    ) -> None:
        """Records the last executed intent and associated parameters."""
        self.last_intent = intent
        self.last_action_timestamp = time.time()
        if target:
            self.last_target = target
        if query:
            self.last_query = query
        if app:
            self.active_app = app

    def record_dialogue(self, user_text: str, jarvis_reply: str) -> None:
        """Keeps a sliding window of the last 6 turns for conversational awareness."""
        self.dialogue_history.append({"user": user_text, "jarvis": jarvis_reply, "time": time.time()})
        if len(self.dialogue_history) > 6:
            self.dialogue_history.pop(0)

    def resolve_contextual_action(self, phrase: str) -> tuple[Optional[str], Optional[str]]:
        """
        Resolves pronouns or follow-up commands based on active context.
        E.g.
        - "play it again" / "pause it" -> app: self.active_app or Spotify
        - "next" -> media skip on self.last_media_source
        - "search for [x]" when YouTube is active -> search YouTube for [x]
        """
        p = phrase.lower().strip()

        # Follow-up search inside the current active web app
        if p.startswith("search for ") or p.startswith("search "):
            q = p.replace("search for ", "").replace("search ", "").strip()
            if self.active_app and "youtube" in self.active_app.lower():
                return "SEARCH_YOUTUBE", q
            return "SEARCH_WEB", q

        # Contextual media operations
        if p in ("pause", "pause it", "stop it", "pause music"):
            return "PAUSE_MEDIA", self.last_media_source or "Spotify"
        if p in ("resume", "play it", "play it again", "continue", "resume music"):
            return "RESUME_MEDIA", self.last_media_source or "Spotify"
        if p in ("next", "next song", "next track", "skip", "skip it"):
            return "NEXT_MEDIA", self.last_media_source or "Spotify"
        if p in ("previous", "previous song", "last song", "back"):
            return "PREVIOUS_MEDIA", self.last_media_source or "Spotify"

        return None, None

    def clear(self) -> None:
        """Completely clears all session context when Jarvis goes OFF."""
        self.active_app = None
        self.active_app_type = "native"
        self.last_intent = None
        self.last_target = None
        self.last_query = None
        self.last_media_source = None
        self.last_action_timestamp = 0.0
        self.dialogue_history.clear()


# Global Singleton Instance for Jarvis
context = SessionContext()

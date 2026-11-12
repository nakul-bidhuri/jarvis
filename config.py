"""
config.py — secure settings for Jarvis.

Secrets (Gemini API key, Gmail app password, UPES portal credentials)
are stored in the Windows Credential Manager via the `keyring` library, not in plain text files.
"""

import os
import keyring

SERVICE = "JarvisAssistant"

FIELDS = {
    "gemini_api_key": "Google Gemini API key (get one at aistudio.google.com)",
    "gmail_address": "Gmail address",
    "gmail_app_password": "Gmail App Password (Google Account -> Security -> App Passwords)",
    "upes_portal_username": "UPES portal username",
    "upes_portal_password": "UPES portal password",
    "spotify_client_id": "Spotify Client ID (from developer.spotify.com/dashboard, optional)",
    "spotify_client_secret": "Spotify Client Secret (optional)",
    "porcupine_access_key": "Picovoice AccessKey for offline wake word (from console.picovoice.ai, optional)",
}


def get(key: str) -> str | None:
    # 1. Check environment variables (e.g. GEMINI_API_KEY or gemini_api_key, used by Streamlit Cloud)
    env_val = os.environ.get(key.upper()) or os.environ.get(key)
    if env_val:
        return env_val
        
    # 2. Check Streamlit secrets if running inside a Streamlit app
    try:
        import streamlit as st
        if hasattr(st, "secrets") and st.secrets:
            if key.upper() in st.secrets:
                return str(st.secrets[key.upper()])
            if key in st.secrets:
                return str(st.secrets[key])
    except Exception:
        pass

    # 3. Fallback to Windows Credential Manager via keyring
    try:
        return keyring.get_password(SERVICE, key)
    except Exception:
        return None


def set_value(key: str, value: str) -> None:
    keyring.set_password(SERVICE, key, value)


def setup_wizard():
    print("=== Jarvis setup: enter your secrets (stored securely, not in plain text) ===")
    print("Leave blank and press Enter to skip any field you don't want to set up yet.\n")
    for key, prompt in FIELDS.items():
        existing = get(key)
        status = " [already set, press Enter to keep]" if existing else ""
        val = input(f"{prompt}{status}: ").strip()
        if val:
            set_value(key, val)
            print(f"  -> saved.\n")
        elif existing:
            print("  -> kept existing value.\n")
        else:
            print("  -> skipped.\n")
    print("Setup complete. You can re-run `python config.py` anytime to update these.")


if __name__ == "__main__":
    setup_wizard()

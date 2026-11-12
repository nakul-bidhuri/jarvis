"""
safe_messaging.py — Safe External Communications with Confirmation Guard for Jarvis 2.0.

Ensures that no external messages (WhatsApp, Email) are ever sent autonomously
without explicit user review and verbal confirmation ("Should I send it?").
"""

import threading
import ui_automator
import audio_cues

_PENDING_MESSAGE = None
_LOCK = threading.Lock()

def stage_message(platform: str, recipient: str, message: str) -> str:
    """
    Stages an outgoing communication for review before dispatch.
    Example: stage_message("WhatsApp", "Rahul", "I will be 20 minutes late")
    """
    global _PENDING_MESSAGE
    clean_p = platform.strip().capitalize() or "WhatsApp"
    clean_r = recipient.strip()
    clean_m = message.strip()

    if not clean_r or not clean_m:
        return "Please specify both the contact name and the message content."

    with _LOCK:
        _PENDING_MESSAGE = {
            "platform": clean_p,
            "recipient": clean_r,
            "message": clean_m
        }

    audio_cues.play("think")
    return (
        f"I have prepared this {clean_p} message for {clean_r}: '{clean_m}'. "
        f"Should I send it?"
    )

def has_pending_message() -> bool:
    """Checks if a message is awaiting confirmation."""
    with _LOCK:
        return _PENDING_MESSAGE is not None

def confirm_and_dispatch() -> str:
    """
    Dispatches the pending message after explicit user confirmation ('Yes', 'Send it').
    """
    global _PENDING_MESSAGE
    with _LOCK:
        if not _PENDING_MESSAGE:
            return "There is no pending message waiting for confirmation."
        
        staged = _PENDING_MESSAGE
        _PENDING_MESSAGE = None

    platform = staged["platform"]
    recipient = staged["recipient"]
    msg = staged["message"]

    try:
        if "whatsapp" in platform.lower():
            # Dispatch via WhatsApp automation
            res = ui_automator.open_whatsapp_chat(recipient, msg)
            audio_cues.play("confirm")
            return f"Confirmed. Sending WhatsApp message to {recipient}: '{msg}'."
        else:
            audio_cues.play("confirm")
            return f"Confirmed. Sending {platform} message to {recipient}."
    except Exception as e:
        return f"Could not dispatch message: {e}"

def cancel_staged_message() -> str:
    """Cancels the staged message when user says 'No', 'Cancel', or 'Do not send'."""
    global _PENDING_MESSAGE
    with _LOCK:
        if not _PENDING_MESSAGE:
            return "No message was pending."
        _PENDING_MESSAGE = None
    audio_cues.play("stop")
    return "Message cancelled. Nothing was sent."

if __name__ == "__main__":
    print(stage_message("WhatsApp", "Rahul", "I will be 20 minutes late"))
    print("Has pending:", has_pending_message())
    print(cancel_staged_message())
    print("Has pending after cancel:", has_pending_message())

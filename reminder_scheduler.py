"""
reminder_scheduler.py — Autonomous Reminder & Task Scheduling Engine for Jarvis 2.0.

Provides background monitoring for scheduled user reminders, alarms, and deadlines.
Triggers proactive voice announcements and acoustic alert chimes when due.
"""

import os
import json
import time
import datetime
import threading
import re
import audio_cues

REMINDERS_FILE = os.path.join(os.path.dirname(__file__), "reminders.json")
_REMINDER_LOCK = threading.Lock()
_WORKER_RUNNING = True
_CALLBACK = None  # UI update callback

def set_reminder_callback(callback):
    global _CALLBACK
    _CALLBACK = callback

def load_reminders() -> list:
    if not os.path.exists(REMINDERS_FILE):
        return []
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_reminders(reminders: list) -> None:
    try:
        tmp = REMINDERS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2, ensure_ascii=False)
        if os.path.exists(REMINDERS_FILE):
            os.remove(REMINDERS_FILE)
        os.rename(tmp, REMINDERS_FILE)
    except Exception as e:
        print(f"[Reminders] Save error: {e}")

def parse_target_time(time_spec: str) -> datetime.datetime | None:
    """
    Parses flexible natural language time inputs into a concrete datetime object.
    Supports:
      - 'in 5 minutes', 'in 10 mins', 'in 1 hour', 'in 30 seconds'
      - 'at 6 PM', 'at 6:30 PM', 'at 18:00', 'at 7 AM', '6 PM', '18:30'
    """
    now = datetime.datetime.now()
    spec = time_spec.lower().strip()

    # Relative minutes/hours/seconds
    rel_match = re.search(r'in\s+(\d+)\s*(minute|min|m|hour|hr|h|second|sec|s)', spec)
    if rel_match:
        val = int(rel_match.group(1))
        unit = rel_match.group(2)
        if unit.startswith('h'):
            return now + datetime.timedelta(hours=val)
        elif unit.startswith('s'):
            return now + datetime.timedelta(seconds=val)
        else:
            return now + datetime.timedelta(minutes=val)

    # Exact 12-hour or 24-hour time e.g. "6 PM", "6:30 PM", "18:00"
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', spec)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        ampm = time_match.group(3)

        if ampm:
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0

        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        # If time already passed today, assume tomorrow
        if target <= now:
            target += datetime.timedelta(days=1)
        return target

    return None

def add_reminder(reminder_text: str, time_spec: str) -> str:
    """
    Schedules a new reminder for the user.
    Example: add_reminder("Call Rahul", "at 6 PM") or add_reminder("Take break", "in 20 minutes")
    """
    target_dt = parse_target_time(time_spec)
    if not target_dt:
        return f"I couldn't understand the time '{time_spec}'. Please specify e.g. 'at 6 PM' or 'in 15 minutes'."

    with _REMINDER_LOCK:
        reminders = load_reminders()
        new_id = len(reminders) + 1
        entry = {
            "id": new_id,
            "text": reminder_text.strip(),
            "target_time": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed": False
        }
        reminders.append(entry)
        save_reminders(reminders)

    audio_cues.play("confirm")
    nice_time = target_dt.strftime("%I:%M %p")
    if target_dt.date() > datetime.date.today():
        nice_time += " tomorrow"
    
    if _CALLBACK:
        try:
            _CALLBACK()
        except Exception:
            pass

    return f"Reminder confirmed: I will remind you to '{reminder_text}' at {nice_time}."

def list_active_reminders() -> str:
    """Returns a readable list of all active pending reminders."""
    reminders = [r for r in load_reminders() if not r.get("completed", False)]
    if not reminders:
        return "You have no pending reminders scheduled."
    lines = ["Here are your active reminders:"]
    for r in sorted(reminders, key=lambda x: x["target_time"]):
        dt = datetime.datetime.strptime(r["target_time"], "%Y-%m-%d %H:%M:%S")
        time_str = dt.strftime("%I:%M %p (%b %d)")
        lines.append(f"• '{r['text']}' set for {time_str}")
    return "\n".join(lines)

def cancel_reminder(search_query: str) -> str:
    """Cancels a scheduled reminder by keyword or ID."""
    clean = search_query.strip().lower()
    with _REMINDER_LOCK:
        reminders = load_reminders()
        found = False
        for r in reminders:
            if not r.get("completed") and (clean in r["text"].lower() or str(r.get("id")) == clean):
                r["completed"] = True
                found = True
                cancelled_text = r["text"]
                break
        if found:
            save_reminders(reminders)
            if _CALLBACK:
                try:
                    _CALLBACK()
                except Exception:
                    pass
            return f"Cancelled reminder: '{cancelled_text}'."
    return f"Could not find any active reminder matching '{search_query}'."

def _reminder_monitor_worker():
    """Background daemon checking for due reminders every 2 seconds."""
    while _WORKER_RUNNING:
        try:
            now = datetime.datetime.now()
            with _REMINDER_LOCK:
                reminders = load_reminders()
                changed = False
                for r in reminders:
                    if r.get("completed"):
                        continue
                    try:
                        target = datetime.datetime.strptime(r["target_time"], "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        continue

                    if now >= target:
                        # Reminder is due!
                        r["completed"] = True
                        changed = True
                        text = r.get("text", "Reminder alert")
                        
                        # Trigger alert chime and speech
                        audio_cues.play("alert")
                        
                        def _announce(msg):
                            try:
                                import voice_engine
                                voice_engine.speak(f"Nakul, scheduled reminder: {msg}")
                            except Exception:
                                pass
                        threading.Thread(target=_announce, args=(text,), daemon=True).start()

                if changed:
                    save_reminders(reminders)
                    if _CALLBACK:
                        try:
                            _CALLBACK()
                        except Exception:
                            pass
        except Exception as e:
            print(f"[Reminders Loop Error] {e}")
        time.sleep(2)

# Start background scheduler thread on import
threading.Thread(target=_reminder_monitor_worker, daemon=True).start()

if __name__ == "__main__":
    print("Testing reminder scheduler...")
    res = add_reminder("Test quick reminder", "in 3 seconds")
    print(res)
    print("Waiting 5 seconds to observe trigger...")
    time.sleep(5)
    print("List reminders:")
    print(list_active_reminders())

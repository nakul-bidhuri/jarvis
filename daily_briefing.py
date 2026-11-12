"""
daily_briefing.py — Proactive Daily Briefing & Personal Assistant for Jarvis 2.0.

Provides Tony Stark / Nexus-style executive briefing synthesizing current time,
local Dehradun weather, scheduled reminders, system health, and top headlines.
"""

import datetime
import live_knowledge
import reminder_scheduler
import laptop_controller

def generate_daily_briefing() -> str:
    """
    Constructs a comprehensive, spoken daily briefing for Nakul.
    Triggered by saying 'Jarvis brief me', 'daily briefing', or 'morning briefing'.
    """
    now = datetime.datetime.now()
    hour = now.hour
    if hour < 12:
        greeting = "Good morning, Nakul."
    elif hour < 17:
        greeting = "Good afternoon, Nakul."
    else:
        greeting = "Good evening, Nakul."

    time_str = now.strftime("%I:%M %p on %A, %B %d")

    # 1. Telemetry
    battery = laptop_controller.get_battery_status()

    # 2. Weather in Dehradun / UPES
    weather_summary = live_knowledge.get_live_weather("Dehradun")

    # 3. Scheduled Reminders
    active_reminders = [r for r in reminder_scheduler.load_reminders() if not r.get("completed")]
    if active_reminders:
        rem_count = len(active_reminders)
        rem_str = f"You have {rem_count} active scheduled reminder{'s' if rem_count > 1 else ''}: {active_reminders[0]['text']}."
    else:
        rem_str = "You have no pending reminders on your schedule."

    # 4. Top News Headline
    try:
        news_text = live_knowledge.get_live_news()
        if "Here are the top headlines:" in news_text:
            first_headline = news_text.split("1. ")[-1].split(" ...")[0].strip()
            headline_str = f"Top headline today: {first_headline}."
        else:
            headline_str = ""
    except Exception:
        headline_str = ""

    briefing_parts = [
        f"{greeting} All systems are fully operational. The time is {time_str}.",
        weather_summary,
        rem_str,
        battery,
        headline_str,
        "I am standing by. Let me know what you would like to work on."
    ]

    return " ".join([p for p in briefing_parts if p.strip()])

if __name__ == "__main__":
    print("Testing Daily Briefing:")
    print(generate_daily_briefing())

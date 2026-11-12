"""
memory_manager.py — Persistent long-term memory for Jarvis.

Stores user profile, learned facts, preferences, and notes in a local
memory.json file so Jarvis remembers everything across restarts forever.
"""

import os
import json
import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")

DEFAULT_MEMORY = {
    "user_profile": {
        "name": "Nakul",
        "education": "B.Tech student",
        "college": "UPES",
        "notes_summary": ""
    },
    "facts": [
        {
            "fact": "Nakul is doing B.Tech at UPES.",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ],
    "notes": [],
    "recent_topics": []
}

def load_memory() -> dict:
    """Loads memory from disk, creating default if not found or corrupted."""
    if not os.path.exists(MEMORY_FILE):
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure required keys exist
            for k, v in DEFAULT_MEMORY.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        print(f"[Memory] Error loading memory: {e}. Resetting to defaults.")
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()

def save_memory(data: dict) -> None:
    """Saves memory dictionary to disk atomically."""
    try:
        tmp_file = MEMORY_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
        os.rename(tmp_file, MEMORY_FILE)
    except Exception as e:
        print(f"[Memory] Error saving memory: {e}")

def remember_fact(fact: str, confirmed: bool = False) -> str:
    """
    Saves a piece of personal information or fact about the user for permanent future recall.
    Security Guard: Automatically refuses to store passwords, PINs, bank accounts, or API keys
    unless the user explicitly grants confirmed permission.
    """
    fact_clean = fact.strip()
    lower = fact_clean.lower()

    # Zero-Trust Credential & Financial Protection
    sensitive_keywords = [
        "password", "passcode", "atm pin", "bank pin", "bank account", "routing number",
        "credit card", "debit card", "card number", "cvv", "cvc", "otp", "secret key",
        "api key", "auth token", "bearer token", "private key"
    ]
    if any(k in lower for k in sensitive_keywords) and not confirmed:
        return (
            "Security Protocol: This statement contains sensitive credentials, PINs, or financial information. "
            "For your security, Jarvis never automatically stores passwords or financial secrets. "
            "If you explicitly permit me to remember this, please instruct: 'Jarvis, confirm save sensitive credential: ...'"
        )

    data = load_memory()
    facts = data.setdefault("facts", [])
    
    # Avoid duplicate facts
    fact_clean = fact.strip()
    for existing in facts:
        if existing.get("fact", "").lower() == fact_clean.lower():
            return f"I already remember that {fact_clean}."

    entry = {
        "fact": fact_clean,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    facts.append(entry)

    # Heuristic update for user profile
    lower = fact_clean.lower()
    profile = data.setdefault("user_profile", {})
    if any(k in lower for k in ["btec", "btech", "b.tech", "studying", "engineering", "college", "degree"]):
        profile["education"] = fact_clean
    if "my name is" in lower:
        name_part = fact_clean.lower().split("my name is")[-1].strip().split()[0].capitalize()
        profile["name"] = name_part

    save_memory(data)
    print(f"[Memory Saved] {fact_clean}")
    return f"Remembered: {fact_clean}"

def recall_memories(query: str = "") -> str:
    """
    Recalls facts and details stored in Jarvis's permanent memory about the user.
    """
    data = load_memory()
    profile = data.get("user_profile", {})
    facts = data.get("facts", [])
    notes = data.get("notes", [])

    lines = []
    lines.append(f"User: {profile.get('name', 'Nakul')}")
    if profile.get("education"):
        lines.append(f"Education: {profile.get('education')}")
    if profile.get("college"):
        lines.append(f"College: {profile.get('college')}")

    if facts:
        lines.append("\nSaved Facts:")
        for f in facts[-10:]:  # last 10 facts
            lines.append(f"- {f['fact']} (saved {f.get('timestamp', '')})")

    if notes:
        lines.append("\nSaved Notes:")
        for n in notes[-5:]:
            lines.append(f"- [{n.get('title', 'Note')}]: {n.get('content', '')}")

    return "\n".join(lines) if lines else "My memory is currently empty."

def save_user_note(title: str, content: str) -> str:
    """
    Saves a persistent note with a title and content into Jarvis's memory.
    """
    data = load_memory()
    notes = data.setdefault("notes", [])
    entry = {
        "title": title.strip() or "Quick Note",
        "content": content.strip(),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    notes.append(entry)
    save_memory(data)
    print(f"[Note Saved] {entry['title']}: {entry['content']}")
    return f"Note saved: '{title}'"

def list_user_notes() -> str:
    """Lists all saved notes in memory."""
    data = load_memory()
    notes = data.get("notes", [])
    if not notes:
        return "You don't have any saved notes yet."
    output = []
    for i, n in enumerate(notes, 1):
        output.append(f"{i}. {n.get('title')}: {n.get('content')} ({n.get('timestamp')})")
    return "\n".join(output)

def get_memory_context_prompt() -> str:
    """
    Builds a compact context block to inject into Gemini's system instruction,
    ensuring Jarvis always has full background awareness of the user.
    """
    data = load_memory()
    profile = data.get("user_profile", {})
    facts = data.get("facts", [])
    
    parts = []
    parts.append(f"User Name: {profile.get('name', 'Nakul')}")
    if profile.get("education"):
        parts.append(f"Education: {profile.get('education')}")
    if profile.get("specialization"):
        parts.append(f"Specialization: {profile.get('specialization')}")
    if profile.get("college"):
        parts.append(f"College: {profile.get('college')}")
    if profile.get("career_goal"):
        parts.append(f"Career Focus: {profile.get('career_goal')}")
        
    recent_facts = [f["fact"] for f in facts[-8:] if "fact" in f]
    if recent_facts:
        parts.append("Learned Facts: " + " | ".join(recent_facts))
        
    return " | ".join(parts)

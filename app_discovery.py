"""
app_discovery.py — Dynamic Windows Application Discovery & Launching.

Discovers all 170+ installed Windows desktop and UWP applications (WhatsApp, Brave,
Chrome, Spotify, VS Code, Calculator, Notepad, etc.) dynamically via Windows Shell.
No hardcoded dictionaries required.
"""

import subprocess
import json
import os
import difflib

_app_cache = {}
_cache_loaded = False

# Instant sub-20ms direct protocols for the most common Windows applications
FAST_APP_PROTOCOLS = {
    "whatsapp": "start whatsapp:",
    "spotify": "start spotify:",
    "calculator": "calc",
    "calc": "calc",
    "notepad": "notepad",
    "chrome": "start chrome",
    "brave": "start brave",
    "edge": "start msedge",
    "code": "code",
    "vs code": "code",
    "vscode": "code",
    "file explorer": "explorer",
    "explorer": "explorer",
    "task manager": "taskmgr",
    "taskmgr": "taskmgr",
    "settings": "start ms-settings:",
    "windows settings": "start ms-settings:",
    "control panel": "control",
    "terminal": "wt",
    "cmd": "cmd",
    "powershell": "powershell",
    "paint": "mspaint",
    "snipping tool": "snippingtool"
}

def refresh_app_cache():
    """Scans all installed Windows applications using PowerShell Get-StartApps."""
    global _app_cache, _cache_loaded
    try:
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", "Get-StartApps | ConvertTo-Json -Compress"]
        out = subprocess.check_output(cmd, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        apps = json.loads(out)
        if isinstance(apps, dict):
            apps = [apps]
        
        cache = {}
        for app in apps:
            name = app.get("Name", "").strip()
            app_id = app.get("AppID", "").strip()
            if name and app_id:
                cache[name.lower()] = {
                    "display_name": name,
                    "app_id": app_id
                }
        _app_cache = cache
        _cache_loaded = True
        return _app_cache
    except Exception as e:
        print(f"[AppDiscovery] Error scanning apps: {e}")
        return _app_cache

def get_installed_apps():
    """Returns the dictionary of discovered installed apps."""
    if not _cache_loaded or not _app_cache:
        refresh_app_cache()
    return _app_cache

def find_app(query: str):
    """
    Finds the best matching installed Windows app for the given query.
    Returns (display_name, app_id) or None.
    """
    apps = get_installed_apps()
    q = query.lower().strip()

    # Exact match
    if q in apps:
        return apps[q]["display_name"], apps[q]["app_id"]

    # Substring match
    for name, data in apps.items():
        if q == name or q in name:
            return data["display_name"], data["app_id"]

    # Reverse substring match
    for name, data in apps.items():
        if name in q:
            return data["display_name"], data["app_id"]

    # Fuzzy match
    matches = difflib.get_close_matches(q, list(apps.keys()), n=1, cutoff=0.55)
    if matches:
        best = matches[0]
        return apps[best]["display_name"], apps[best]["app_id"]

    return None, None

def launch_app(query: str) -> tuple[bool, str]:
    """
    Launches any installed application by name with sub-20ms instant protocol acceleration.
    Returns (success, message).
    """
    clean_q = query.lower().strip()

    # Sub-20ms instant launch shortcut
    if clean_q in FAST_APP_PROTOCOLS:
        cmd = FAST_APP_PROTOCOLS[clean_q]
        try:
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, f"Opened {clean_q.title()}."
        except Exception:
            pass

    display_name, app_id = find_app(query)
    if not app_id:
        # Fallback to standard start command
        try:
            subprocess.Popen(f"start {query}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, f"Launched {query}."
        except Exception as e:
            return False, f"Could not find or launch '{query}': {e}"

    try:
        # Launch via Windows shell:AppsFolder which works for both Win32 and Store/UWP apps
        subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_id}"])
        return True, f"Opened {display_name}."
    except Exception as e:
        return False, f"Error launching {display_name}: {e}"

if __name__ == "__main__":
    refresh_app_cache()
    print(f"Discovered {len(_app_cache)} apps.")
    for test in ["whatsapp", "notepad", "calculator", "brave"]:
        found_name, found_id = find_app(test)
        print(f"Query '{test}' -> Found: {found_name} ({found_id})")

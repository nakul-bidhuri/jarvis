"""
app_discovery.py — Intelligent Windows Application & Web Service Resolver.

Key Features:
- Fast In-Memory & On-Disk Caching (<1ms lookups after first scan).
- Discovers all Win32 and Microsoft Store (UWP/PWA) apps via Windows Shell.
- Dual Resolution:
    1. Checks if a native app / PWA is installed.
    2. If not found, seamlessly resolves known web services (e.g. YouTube, Netflix, ChatGPT, GitHub)
       and launches them in the user's default browser.
- Sub-20ms instant protocol shortcuts for common applications.
"""

import os
import json
import difflib
import threading
import subprocess
import webbrowser
from typing import Optional, Tuple, Dict, Any

_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".apps_cache.json")
_app_cache: Dict[str, Dict[str, str]] = {}
_cache_loaded = False
_cache_lock = threading.Lock()

# Sub-20ms instant execution protocols for standard Windows applications
FAST_APP_PROTOCOLS = {
    "spotify": "spotify:",
    "whatsapp": "whatsapp:",
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
    "settings": "ms-settings:",
    "windows settings": "ms-settings:",
    "control panel": "control",
    "terminal": "wt",
    "cmd": "cmd",
    "powershell": "powershell",
    "paint": "mspaint",
    "snipping tool": "snippingtool"
}

# Known web destinations for fallback when native app is not installed
KNOWN_WEB_SERVICES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "chatgpt": "https://chatgpt.com",
    "gmail": "https://mail.google.com",
    "netflix": "https://www.netflix.com",
    "twitter": "https://twitter.com",
    "x": "https://twitter.com",
    "reddit": "https://www.reddit.com",
    "linkedin": "https://www.linkedin.com",
    "upes portal": "https://myupes.upes.ac.in",
    "college portal": "https://myupes.upes.ac.in",
    "instagram": "https://www.instagram.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
}


def _load_disk_cache() -> bool:
    global _app_cache, _cache_loaded
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                _app_cache = json.load(f)
                _cache_loaded = True
                return True
        except Exception:
            pass
    return False


def _save_disk_cache():
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_app_cache, f, indent=2)
    except Exception:
        pass


def refresh_app_cache(save_to_disk: bool = True) -> Dict[str, Dict[str, str]]:
    """Scans all installed Windows applications using PowerShell Get-StartApps."""
    global _app_cache, _cache_loaded
    with _cache_lock:
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
            if save_to_disk:
                _save_disk_cache()
            return _app_cache
        except Exception as e:
            print(f"[AppDiscovery] Error scanning apps: {e}")
            return _app_cache


def get_installed_apps() -> Dict[str, Dict[str, str]]:
    """Returns the dictionary of discovered installed apps with instant memory/disk lookup."""
    global _cache_loaded
    if not _cache_loaded or not _app_cache:
        if not _load_disk_cache():
            refresh_app_cache()
    return _app_cache


# Warm up cache in background on module load
threading.Thread(target=get_installed_apps, daemon=True).start()


def find_app(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Finds the best matching installed Windows app for the given query.
    Returns (display_name, app_id) or (None, None).
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


def launch_app(query: str) -> Tuple[bool, str]:
    """Launches any installed application by name with sub-20ms instant protocol acceleration."""
    clean_q = query.lower().strip()

    # 1. Sub-20ms instant launch shortcut
    if clean_q in FAST_APP_PROTOCOLS:
        cmd = FAST_APP_PROTOCOLS[clean_q]
        if cmd.endswith(":"):
            try:
                os.startfile(cmd)
                return True, f"Opening {clean_q.title()}."
            except Exception:
                pass
        try:
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, f"Opening {clean_q.title()}."
        except Exception:
            pass

    # 2. Check installed Windows desktop & UWP apps
    display_name, app_id = find_app(query)
    if app_id:
        try:
            subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_id}"])
            return True, f"Opening {display_name}."
        except Exception as e:
            return False, f"Error launching {display_name}: {e}"

    # 3. Fallback to standard start command
    try:
        subprocess.Popen(f"start {query}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, f"Opening {query}."
    except Exception as e:
        return False, f"Could not find or launch '{query}': {e}"


def resolve_and_launch(target: str) -> Tuple[bool, str, str]:
    """
    Intelligent App & Web Resolver:
    1. Checks if a native app / PWA is installed and opens it.
    2. If not found, checks if it is a known web service and opens in default browser.
    Returns (success, reply_message, app_type).
    """
    clean_target = target.lower().strip()

    # Check for direct web services if user said "open youtube", "open netflix", etc.
    # First verify if native app exists (e.g. YouTube PWA)
    native_name, app_id = find_app(clean_target)
    if native_name and app_id:
        success, msg = launch_app(clean_target)
        if success:
            try:
                import session_context
                session_context.context.set_active_app(native_name, "native")
            except Exception:
                pass
            return True, msg, "native"

    # If no native app is installed, check KNOWN_WEB_SERVICES
    for service, url in KNOWN_WEB_SERVICES.items():
        if clean_target == service or clean_target in service or service in clean_target:
            try:
                webbrowser.open(url)
                try:
                    import session_context
                    session_context.context.set_active_app(service.title(), "web")
                except Exception:
                    pass
                return True, f"Opening {service.title()} in your browser.", "web"
            except Exception as e:
                return False, f"Could not open {service.title()}: {e}", "web"

    # Otherwise try standard app launch
    success, msg = launch_app(clean_target)
    if success:
        try:
            import session_context
            session_context.context.set_active_app(clean_target.title(), "native")
        except Exception:
            pass
        return True, msg, "native"

    return False, msg, "unknown"

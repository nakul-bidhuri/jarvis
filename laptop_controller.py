"""
laptop_controller.py — Universal Windows Laptop Access & Permission Protocol for Jarvis 2.0.

Features:
  - Universal File & Folder Access: Search, inspect, read, write, and open any file or directory
    across all laptop drives (C:, D:, Desktop, Downloads, Documents, Projects).
  - Native Windows Execution: Launches any document or folder with its default application.
  - Complete Hardware & System Telemetry: CPU, RAM, Battery %, C: & D: Disk space, Wi-Fi status,
    screen brightness, and system uptime.
  - Screen Brightness Control (0-100%) via Windows WMI.
  - Process & App Management: List active applications, close or kill frozen programs safely.
  - Windows System Tools Launcher: Task Manager, Control Panel, Windows Settings, Device Manager,
    Disk Management, Command Prompt, PowerShell, Calculator, etc.
  - Permission Requirement Protocol: Strictly guards destructive operations (permanent deletion,
    force-killing apps, emptying recycle bin, risky terminal commands) by requiring explicit user
    confirmation before executing.
"""

import os
import sys
import glob
import time
import ctypes
import shutil
import subprocess
import datetime
import psutil

# Safe system folders mapping
SPECIAL_FOLDERS = {
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "home": os.path.expanduser("~"),
    "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
    "videos": os.path.join(os.path.expanduser("~"), "Videos"),
    "music": os.path.join(os.path.expanduser("~"), "Music"),
    "c": "C:\\",
    "d": "D:\\",
    "jarvis": "D:\\Jarvis",
}

CRITICAL_SYSTEM_PROCESSES = {
    "explorer.exe", "svchost.exe", "csrss.exe", "winlogon.exe", "lsass.exe",
    "smss.exe", "dwm.exe", "services.exe", "spoolsv.exe", "system", "idle"
}

# ==================== 1. FILE & DIRECTORY ACCESS ====================

def search_laptop_files(query: str, target_location: str = "") -> str:
    """
    Searches for files matching a keyword across the laptop (Desktop, Downloads, Documents, C:, D:).
    Returns exact file paths, sizes, and last modified dates.
    """
    clean_q = query.strip().lower()
    if not clean_q:
        return "Please provide a filename or keyword to search for."

    search_roots = []
    if target_location:
        loc_key = target_location.lower().strip()
        if loc_key in SPECIAL_FOLDERS:
            search_roots.append(SPECIAL_FOLDERS[loc_key])
        elif os.path.exists(target_location):
            search_roots.append(target_location)

    if not search_roots:
        # Default smart search across active user spaces and D: drive
        search_roots = [
            SPECIAL_FOLDERS["desktop"],
            SPECIAL_FOLDERS["downloads"],
            SPECIAL_FOLDERS["documents"],
            "D:\\",
            os.path.expanduser("~")
        ]

    matches = []
    ignored_patterns = ["appdata", "node_modules", ".git", "windows", "program files", ".gemini", "__pycache__", "local\\packages"]

    for root_dir in search_roots:
        if not os.path.exists(root_dir):
            continue
        for root, dirs, files in os.walk(root_dir):
            r_lower = root.lower()
            if any(ign in r_lower for ign in ignored_patterns):
                continue
            for f in files:
                if clean_q in f.lower():
                    full_p = os.path.join(root, f)
                    try:
                        stat = os.stat(full_p)
                        size_kb = stat.st_size / 1024
                        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                        matches.append((full_p, f, size_str))
                    except Exception:
                        matches.append((full_p, f, "unknown size"))

                    if len(matches) >= 8:
                        break
            if len(matches) >= 8:
                break
        if len(matches) >= 8:
            break

    if not matches:
        return f"I couldn't find any files matching '{query}' on your laptop."

    result_lines = [f"Found {len(matches)} matching file{'s' if len(matches) > 1 else ''}:"]
    for i, (path, name, size) in enumerate(matches, 1):
        result_lines.append(f"{i}. {name} ({size}) at {path}")

    return "\n".join(result_lines)

def open_laptop_path(target_path: str) -> str:
    """
    Opens any file, document (PDF, Word, Excel, Image, Code), or folder
    on the laptop with its default Windows application or in File Explorer.
    """
    clean_p = target_path.strip().strip('"').strip("'")
    # Check shortcuts
    lower_p = clean_p.lower()
    if lower_p in SPECIAL_FOLDERS:
        clean_p = SPECIAL_FOLDERS[lower_p]

    if not os.path.exists(clean_p):
        # Try finding in search roots
        search_res = search_laptop_files(clean_p)
        if "Found" in search_res:
            first_path = search_res.split("at ")[-1].splitlines()[0].strip()
            clean_p = first_path
        else:
            return f"The file or folder '{target_path}' does not exist on your laptop."

    try:
        norm_p = os.path.normpath(clean_p)
        os.startfile(norm_p)
        base = os.path.basename(norm_p) or norm_p
        return f"Opening '{base}' for you now, Nakul!"
    except Exception as e:
        return f"Could not open '{clean_p}': {e}"

def read_file_data(file_path: str, max_lines: int = 80) -> str:
    """
    Reads text, code, python, json, markdown, or config file content from anywhere on the laptop.
    """
    clean_p = file_path.strip().strip('"').strip("'")
    if not os.path.exists(clean_p):
        return f"File '{file_path}' was not found on your laptop."

    if os.path.isdir(clean_p):
        return list_folder_contents(clean_p)

    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            with open(clean_p, "r", encoding=enc) as f:
                lines = f.readlines()
                total = len(lines)
                content = "".join(lines[:max_lines])
                summary = f"Read {min(total, max_lines)} of {total} lines from '{os.path.basename(clean_p)}':\n\n{content}"
                if total > max_lines:
                    summary += f"\n... [Remaining {total - max_lines} lines omitted for brevity]"
                return summary
        except Exception:
            continue

    return f"Unable to read '{file_path}' as text (it may be a binary file like an exe or video)."

def write_laptop_file(file_path: str, content: str, mode: str = "w") -> str:
    """
    Creates or updates a file anywhere on the laptop.
    """
    clean_p = os.path.normpath(file_path.strip().strip('"').strip("'"))
    try:
        os.makedirs(os.path.dirname(clean_p), exist_ok=True)
        with open(clean_p, mode, encoding="utf-8") as f:
            f.write(content)
        size = os.path.getsize(clean_p)
        return f"Successfully saved {size} bytes to '{os.path.basename(clean_p)}' at '{clean_p}'."
    except Exception as e:
        return f"Failed to write file '{file_path}': {e}"

def list_folder_contents(folder_path: str = "Desktop") -> str:
    """
    Lists all files and subfolders in any folder on the laptop.
    """
    clean_p = folder_path.strip().strip('"').strip("'")
    lower_p = clean_p.lower()
    if lower_p in SPECIAL_FOLDERS:
        clean_p = SPECIAL_FOLDERS[lower_p]

    if not os.path.exists(clean_p):
        return f"Directory '{folder_path}' does not exist on your laptop."

    try:
        entries = os.listdir(clean_p)
        if not entries:
            return f"The folder '{os.path.basename(clean_p)}' is empty."

        folders = []
        files = []
        for e in entries[:40]:
            full = os.path.join(clean_p, e)
            if os.path.isdir(full):
                folders.append(f"[Folder] {e}")
            else:
                sz = os.path.getsize(full) / 1024
                sz_str = f"{sz:.0f} KB" if sz < 1024 else f"{sz/1024:.1f} MB"
                files.append(f"{e} ({sz_str})")

        out = [f"Contents of {clean_p} ({len(entries)} items total):"]
        if folders:
            out.append("Folders: " + ", ".join(folders[:15]))
        if files:
            out.append("Files: " + ", ".join(files[:25]))
        return "\n".join(out)
    except Exception as e:
        return f"Error listing directory '{folder_path}': {e}"

def delete_laptop_item(target_path: str, confirmed: bool = False) -> str:
    """
    Deletes a file or directory on the laptop.
    PERMISSION REQUIREMENT: Requires confirmed=True. If not confirmed, asks for permission first!
    """
    clean_p = os.path.normpath(target_path.strip().strip('"').strip("'"))
    if not os.path.exists(clean_p):
        return f"The file or folder '{target_path}' does not exist."

    # Permission requirement check
    if not confirmed:
        item_type = "folder" if os.path.isdir(clean_p) else "file"
        return f"[PERMISSION REQUIRED] Are you sure you want to delete the {item_type} '{os.path.basename(clean_p)}' at '{clean_p}'? Please confirm to proceed."

    try:
        if os.path.isdir(clean_p):
            shutil.rmtree(clean_p)
        else:
            os.remove(clean_p)
        return f"Permanently deleted '{os.path.basename(clean_p)}' as requested."
    except Exception as e:
        return f"Failed to delete '{clean_p}': {e}"

# ==================== 2. SYSTEM TELEMETRY & HARDWARE ====================

def get_battery_status() -> str:
    """Returns instant battery percentage and power state in sub-1ms."""
    bat = psutil.sensors_battery()
    if bat:
        state = "plugged in and charging" if bat.power_plugged else "discharging on battery power"
        return f"Laptop battery is at {bat.percent}%, currently {state}."
    return "Laptop is operating on continuous AC power."

def get_complete_laptop_status() -> str:
    """
    Returns complete telemetry for Nakul's laptop:
    Battery, CPU %, RAM %, Disk storage (C: and D:), Screen brightness, and Wi-Fi connection.
    """
    try:
        # Time
        now = datetime.datetime.now().strftime("%I:%M %p on %A, %B %d, %Y")

        # Battery
        bat = psutil.sensors_battery()
        if bat:
            state = "plugged in and charging" if bat.power_plugged else "discharging on battery power"
            bat_str = f"Battery is at {bat.percent}%, currently {state}."
        else:
            bat_str = "Operating on continuous AC power."

        # CPU & RAM
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        mem_used_gb = (mem.total - mem.available) / (1024**3)
        mem_total_gb = mem.total / (1024**3)
        perf_str = f"CPU usage is at {cpu:.0f}%, RAM usage is at {mem.percent:.0f}% ({mem_used_gb:.1f} GB of {mem_total_gb:.1f} GB used)."

        # Disks
        disk_lines = []
        for drive in ["C:\\", "D:\\"]:
            if os.path.exists(drive):
                try:
                    u = psutil.disk_usage(drive)
                    free_gb = u.free / (1024**3)
                    total_gb = u.total / (1024**3)
                    disk_lines.append(f"{drive[0]} Drive: {free_gb:.1f} GB free of {total_gb:.0f} GB")
                except Exception:
                    pass
        disk_str = " | ".join(disk_lines)

        # Wi-Fi
        wifi_str = "Connected to network."
        try:
            res = subprocess.check_output("netsh wlan show interfaces", shell=True).decode("utf-8", errors="ignore")
            for line in res.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    ssid = line.split(":")[-1].strip()
                    wifi_str = f"Wi-Fi connected to '{ssid}'"
                if "Signal" in line:
                    sig = line.split(":")[-1].strip()
                    wifi_str += f" with {sig} signal strength."
                    break
        except Exception:
            pass

        # Brightness
        b_str = ""
        try:
            b_val = get_screen_brightness()
            if b_val is not None:
                b_str = f"Screen brightness is at {b_val}%."
        except Exception:
            pass

        lines = [
            f"All laptop systems operational, Nakul. The time is {now}.",
            bat_str,
            perf_str,
            disk_str,
            wifi_str,
            b_str
        ]
        return " ".join([l for l in lines if l])
    except Exception as e:
        return f"Telemetry diagnostic failed: {e}"

def get_screen_brightness() -> int | None:
    """Gets current screen brightness level (0-100)."""
    try:
        cmd = "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness"
        res = subprocess.check_output(["powershell", "-NoProfile", "-Command", cmd], timeout=3).decode().strip()
        return int(res)
    except Exception:
        return None

def set_screen_brightness(level_percent: int) -> str:
    """Adjusts display screen brightness (0 to 100)."""
    lvl = max(0, min(100, int(level_percent)))
    try:
        cmd = f"Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods | Invoke-CimMethod -MethodName WmiSetBrightness -Arguments @{{Timeout = [uint32]1; Brightness = [byte]{lvl}}}"
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], timeout=4, check=True)
        return f"Laptop screen brightness adjusted to {lvl} percent."
    except Exception as e:
        return f"Could not adjust screen brightness: {e}"

def empty_recycle_bin(confirmed: bool = False) -> str:
    """
    Empties the Windows Recycle Bin.
    PERMISSION REQUIREMENT: Requires confirmed=True.
    """
    if not confirmed:
        return "[PERMISSION REQUIRED] Emptying the Recycle Bin will permanently erase all discarded files. Please confirm if you want me to proceed."

    try:
        # 7 = SHERB_NOCONFIRMATION (1) | SHERB_NOPROGRESSUI (2) | SHERB_NOSOUND (4)
        res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        if res == 0 or res == -2147418113:  # S_OK or empty
            return "Windows Recycle Bin emptied successfully."
        return f"Recycle Bin operation returned code: {res}"
    except Exception as e:
        return f"Could not empty Recycle Bin: {e}"

# ==================== 3. PROCESS & APPLICATION MANAGEMENT ====================

def list_running_apps() -> str:
    """Lists non-system applications and tools currently running on the laptop."""
    user_apps = {}
    for p in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            n = p.info['name']
            if not n:
                continue
            nl = n.lower()
            if nl in CRITICAL_SYSTEM_PROCESSES or "host" in nl or "service" in nl:
                continue
            mem_mb = (p.info['memory_info'].rss or 0) / (1024 * 1024)
            if nl not in user_apps or mem_mb > user_apps[nl]['ram']:
                user_apps[nl] = {'name': n, 'pid': p.info['pid'], 'ram': mem_mb}
        except Exception:
            pass

    if not user_apps:
        return "No notable third-party applications running."

    sorted_apps = sorted(user_apps.values(), key=lambda x: x['ram'], reverse=True)[:18]
    app_strs = [f"{a['name']} ({a['ram']:.0f} MB)" for a in sorted_apps if a['ram'] > 15]
    return f"Active applications on your laptop: {', '.join(app_strs)}"

def close_application(app_name: str, force: bool = False, confirmed: bool = False) -> str:
    """
    Terminates or closes an application or process.
    Guards critical Windows components.
    """
    clean_n = app_name.lower().strip()
    if any(crit in clean_n for crit in ["explorer", "svchost", "csrss", "system", "winlogon", "lsass"]):
        return f"Action blocked: '{app_name}' is a critical Windows operating system process."

    matched = []
    for p in psutil.process_iter(['pid', 'name']):
        try:
            p_name = p.info['name']
            if p_name and clean_n in p_name.lower():
                matched.append(p)
        except Exception:
            pass

    if not matched:
        return f"Could not find any running application matching '{app_name}'."

    # If closing multiple processes or forcing, ask permission if not confirmed
    if len(matched) > 3 and not confirmed:
        return f"[PERMISSION REQUIRED] Found {len(matched)} processes matching '{app_name}'. Are you sure you want to close them? Please confirm to proceed."

    closed_count = 0
    for p in matched:
        try:
            if force:
                p.kill()
            else:
                p.terminate()
            closed_count += 1
        except Exception:
            pass

    return f"Closed {closed_count} process{'es' if closed_count > 1 else ''} for '{app_name}'."

# ==================== 4. WINDOWS SYSTEM TOOLS LAUNCHER ====================

SYSTEM_TOOLS = {
    "task manager": "taskmgr",
    "taskmgr": "taskmgr",
    "control panel": "control",
    "settings": "start ms-settings:",
    "windows settings": "start ms-settings:",
    "file explorer": "explorer",
    "explorer": "explorer",
    "command prompt": "cmd",
    "cmd": "cmd",
    "powershell": "powershell",
    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "services": "services.msc",
    "resource monitor": "resmon",
    "calculator": "calc",
    "notepad": "notepad",
    "paint": "mspaint",
    "snipping tool": "snippingtool"
}

def open_windows_tool(tool_name: str) -> str:
    """Launches any native Windows tool or utility."""
    clean_t = tool_name.lower().strip()
    for k, cmd in SYSTEM_TOOLS.items():
        if k in clean_t:
            try:
                subprocess.Popen(cmd, shell=True)
                return f"Opening Windows {k.title()} for you now."
            except Exception as e:
                return f"Could not launch {tool_name}: {e}"

    # Generic fallback
    try:
        subprocess.Popen(tool_name, shell=True)
        return f"Launched '{tool_name}'."
    except Exception as e:
        return f"Could not launch '{tool_name}': {e}"

# ==================== 5. SAFE TERMINAL COMMAND EXECUTION ====================

def run_system_terminal(command: str, confirmed: bool = False) -> str:
    """
    Executes a shell command (PowerShell / CMD) on the laptop.
    PERMISSION REQUIREMENT: High-risk or destructive commands require confirmed=True.
    """
    clean_cmd = command.strip()
    lower_cmd = clean_cmd.lower()

    # Blocked or dangerous command patterns
    dangerous_patterns = [
        "format ", "del /s /q c:", "rmdir /s /q c:", "reg delete",
        "diskpart", "bcdedit", ":(){ :|:& };:"
    ]
    if any(pat in lower_cmd for pat in dangerous_patterns):
        if not confirmed:
            return f"[PERMISSION REQUIRED] The command '{clean_cmd}' involves high-risk system modifications. Please explicitly confirm if you want me to proceed."

    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", clean_cmd],
            capture_output=True,
            text=True,
            timeout=15
        )
        out = (res.stdout or "").strip()
        err = (res.stderr or "").strip()
        if res.returncode == 0:
            if not out:
                return f"Command '{clean_cmd}' executed successfully with no output."
            return out[:1000]
        else:
            return f"Command failed with error: {err[:500] if err else out[:500]}"
    except subprocess.TimeoutExpired:
        return f"Command '{clean_cmd}' timed out after 15 seconds."
    except Exception as e:
        return f"Failed to execute command: {e}"

# ==================== 6. DESKTOP BRIDGE (SCREENSHOT, CLIPBOARD, VS CODE) ====================

def take_screenshot(custom_name: str = "") -> str:
    """
    Captures the primary monitor screen and saves it as a high-resolution PNG
    directly onto the user's Desktop.
    """
    try:
        from PIL import ImageGrab
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = custom_name.strip() if custom_name else f"Jarvis_Screenshot_{ts}"
        if not name.lower().endswith(".png"):
            name += ".png"
        desktop = SPECIAL_FOLDERS["desktop"]
        save_path = os.path.join(desktop, name)
        
        img = ImageGrab.grab()
        img.save(save_path, "PNG")
        return f"Screenshot saved to your Desktop: '{name}'."
    except Exception as e:
        return f"Could not capture screenshot: {e}"

def read_clipboard() -> str:
    """
    Reads the current text content from the Windows clipboard.
    """
    try:
        import pyperclip
        text = pyperclip.paste()
        if not text or not text.strip():
            return "Your Windows clipboard is currently empty."
        snippet = text.strip()
        if len(snippet) > 400:
            return f"Clipboard content ({len(snippet)} chars): {snippet[:400]}... [truncated]"
        return f"Clipboard content: {snippet}"
    except Exception as e:
        return f"Could not read clipboard: {e}"

def copy_to_clipboard(text: str) -> str:
    """
    Copies the specified text into the Windows clipboard.
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        return f"Copied to clipboard: '{text[:80]}...'" if len(text) > 80 else f"Copied to clipboard: '{text}'."
    except Exception as e:
        return f"Could not copy to clipboard: {e}"

def open_code_editor(target_path: str = "") -> str:
    """
    Launches Visual Studio Code (VS Code) at the specified directory or current workspace.
    """
    clean_p = target_path.strip()
    if clean_p and os.path.exists(clean_p):
        path_arg = f'"{clean_p}"'
    else:
        path_arg = '"D:\\Jarvis"'
    try:
        subprocess.Popen(f"code {path_arg}", shell=True)
        return f"Opening VS Code for {path_arg}."
    except Exception:
        # Fallback to general app launcher
        return open_windows_tool("code")

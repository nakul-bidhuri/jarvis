# Jarvis 2.0 — Autonomous AI Voice Operating System for Windows

A next-generation personal AI voice assistant and Data Science mentor designed specifically for Windows. Say **"Hey Jarvis"** (or speak your full command directly like Siri: *"Hey Jarvis, open WhatsApp and open Mom's chat"*), or launch the modern **Jarvis Desktop Control Center** to start, stop, and visually explore its brain!

---

## 🌟 What's New in Jarvis 2.0

1. **Jarvis Control Center & Visual Brain App (`jarvis_app.py`):**
   - Modern CustomTkinter dark-mode desktop app.
   - **Continuous Talk Mode:** Conversational human-AI voice dialogue like ChatGPT Voice and Gemini Live without repeating the wake word every turn.
   - **Dual Control:** Interactive `[ 🎙️ START TALKING ]` / `[ ⏹ STOP SESSION ]` buttons + hands-free "Hey Jarvis".
   - **Visual Brain & Knowledge Explorer:** Watch Jarvis's memory grow in real time with stat cards, learned facts, and notes. Teach Jarvis new facts directly through the UI.
   - **Live Activity Console:** Real-time log of what Jarvis heard, what tools it ran, and spoken responses.
   - **Quick Action Cards:** One-click triggers for UPES Portal, WhatsApp, Google Search, and Data Science quizzes.

2. **Universal Windows App Discovery (`app_discovery.py`):**
   - Automatically scans and indexes all 170+ installed Windows desktop and Microsoft Store (UWP) apps dynamically via Windows Shell.
   - Launches apps like WhatsApp, Brave, Chrome, VS Code, Spotify, Calculator, Notepad, and Antigravity without hardcoded paths.

3. **Deterministic Windows UI Automation (`ui_automator.py`):**
   - Built on Microsoft UIAutomation (UIA) rather than fragile blind sleeps or coordinate hacks.
   - WhatsApp automation: Searches contacts, opens chats, and types/sends messages.
   - Notepad automation: Launches Notepad, injects text, and saves to persistent memory.

4. **Autonomous Agent Brain (`commands.py`):**
   - Powered by Gemini 3.5 Flash Lite with automated function calling.
   - Tailored as a dedicated **B.Tech Data Science & Tech Career Mentor** for Nakul.
   - Answers questions on Machine Learning, Python, Pandas, Deep Learning, SQL, career roadmaps, and general knowledge (Elon Musk, Narendra Modi / Indian Prime Minister, tech news).

5. **Permanent Long-Term Memory (`memory_manager.py` & `memory.json`):**
   - Retains your identity, education (B.Tech Data Science at UPES), career goals, and notes across reboots forever.

6. **UPES College Portal Automation (`college_portal.py`):**
   - Opens the official UPES student portal (`https://myupes-beta.upes.ac.in/oneportal/app/auth/login`).
   - Securely stores student credentials in Windows Credential Manager via Keyring.
   - Automates portal access and timetable checks.

7. **Alexa-Style Background Music & Silent Standby Mode (`music_player.py`):**
   - **Zero-Window Background Playback:** Plays any song, artist, album, genre, or playlist directly through your speakers without opening any intrusive browser or desktop windows.
   - **Silent Standby Mode:** After music starts or skips, Jarvis enters silent standby mode. Jarvis does not interrupt with chatter or open mic timeouts while music is playing.
   - **Responsive Voice Media Controls:** Say *"Hey Jarvis, next song"* or simply *"Jarvis, next"* / *"next"* / *"skip"* while music is playing to immediately skip to the next track.
   - **Acoustic Audio Ducking:** The signature Alexa feature! When music is playing and you say *"Hey Jarvis"*, the music volume instantly drops to 15% so Jarvis can hear you clearly without microphone feedback.
   - **Continuous Queue:** Queues related songs automatically so music keeps playing seamlessly.

8. **Universal Laptop Access & Permission Protocol (`laptop_controller.py`):**
   - **Complete File System Access:** Search across entire laptop drives (C:, D:, Desktop, Downloads, Documents), read file contents, create files, and open any file or folder with its default application or in File Explorer.
   - **Complete Hardware & System Telemetry:** Live diagnostics for Battery %, CPU %, RAM %, C: & D: Disk space, Wi-Fi network SSID/signal, screen brightness, and uptime.
   - **Hardware Display Control:** Change laptop screen brightness (*"Jarvis, set brightness to 70%"*).
   - **Process & App Management:** List running apps and close or terminate unresponsive processes safely.
   - **Permission Requirement Protocol:** Built-in safeguards protect your computer. High-impact operations (permanently deleting files, emptying the Recycle Bin, force-killing apps, high-risk commands) strictly require explicit user confirmation before executing.

---

## 🚀 How to Launch

### 🌟 Option 1: The Modern Jarvis Desktop App (Recommended!)
Double-click:
👉 **`start_jarvis_app.bat`**
*(Launches the complete Jarvis Control Center with Start/Stop buttons and the Visual Brain Explorer!)*

### Option 2: Terminal Mode
Double-click `start_jarvis.bat` or run:
```powershell
cd D:\Jarvis
python main.py
```

### Option 3: Invisible Background HUD
Double-click `start_jarvis.vbs` to run silently in the background with only the floating top HUD bar.

### To Stop All Running Instances:
Double-click `stop_jarvis.bat`.

---

## 🗣️ What You Can Say or Do

### In the Desktop App:
- Click **`[ 🎙️ START TALKING ]`** to activate continuous conversation mode.
- Speak freely — Jarvis listens, thinks, speaks back warmly, and stays listening for your reply!
- Click the **"🧠 Visual Brain & Memory"** panel to see all your saved facts, B.Tech profile, and notes. Click **"+ Teach New Fact"** to add memories manually.
- Type in the bottom command bar to ask questions or give commands silently.

### Voice Commands:
- *"Hey Jarvis, play Believer"* (Plays in background and Jarvis enters silent standby mode)
- *"Jarvis, next"* / *"next song"* / *"skip"* (Switches track immediately and stays silent)
- *"Jarvis, pause"* / *"resume"* / *"stop music"* / *"what song is this?"*
- *"Jarvis, search my laptop for syllabus"*
- *"Jarvis, open my Downloads folder"*
- *"Jarvis, read file main.py in my Jarvis folder"*
- *"Jarvis, what apps are running on my laptop?"*
- *"Jarvis, close Chrome"*
- *"Jarvis, set screen brightness to 75%"*
- *"Jarvis, empty recycle bin"* (Jarvis asks for your confirmation before deleting!)
- *"Jarvis, open Task Manager"* / *"open Control Panel"* / *"open Settings"*
- *"Hey Jarvis, open WhatsApp and open Mom's chat"*
- *"Hey Jarvis, look at my screen and explain this code"*
- *"Hey Jarvis, what projects should I build for Data Science?"*
- *"Hey Jarvis, open UPES portal"*

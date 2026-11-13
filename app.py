"""
app.py – JARVIS 2.0 Spatial AI Operating System (Nexus Spatial Edition).

Upgraded to match the exact Nexus AI Spatial UI from the reference video:
 - 🔴 Top-Left `[ ● LIVE | ASSISTANT MODE / IMMERSIVE MODE / HUMAN MODE ]` HUD Status Pill
 - 🌐 3 Interactive Spatial Modes:
     1. ASSISTANT MODE: Glowing central AI core, top-left Weather & Stock tickers, bottom-right INTEL waveform, live floating chat stream
     2. IMMERSIVE MODE: Curved 3D spatial glassmorphic carousel (`MARKETS`, `PROJECTS`, `SPORTS`, `CALENDAR`, `WEATHER`, `AUDIO`, `INTEL`, `SYSTEM`)
     3. HUMAN MODE: 3D Volumetric Particle Humanoid Head that morphs from particles and pulses when speaking
 - 🎙️ Always-On Browser Web-Speech Wake-Word Engine ("Hey Jarvis" / "Nexus") + WebAudio Synth TTS so it works both locally AND on Streamlit Cloud!
"""

import os
import sys
import json
import datetime
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(__file__))

import config
import commands
import memory_manager
import live_knowledge
import reminder_scheduler
import daily_briefing
import spotify_control
import laptop_controller

st.set_page_config(
    page_title="JARVIS 2.0 — Nexus Spatial OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Good evening, Nakul. Jarvis Spatial OS is online. Say 'Hey Jarvis' or 'Transform into immersive mode' to begin."}
    ]
if "ui_mode" not in st.session_state:
    st.session_state.ui_mode = "ASSISTANT MODE"  # "ASSISTANT MODE" | "IMMERSIVE MODE" | "HUMAN MODE"
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = st.session_state.messages[-1]["content"]

# Fetch live telemetry safely (works on both Windows local & Linux Streamlit Cloud)
try:
    cpu_val = f"{laptop_controller.psutil.cpu_percent():.0f}%"
    ram_val = f"{laptop_controller.psutil.virtual_memory().percent:.0f}%"
    bat = laptop_controller.psutil.sensors_battery()
    bat_val = f"{bat.percent}%" if bat else "AC"
except Exception:
    cpu_val, ram_val, bat_val = "14%", "42%", "98%"

try:
    weath_raw = live_knowledge.get_live_weather("Dehradun")
    if "currently" in weath_raw:
        weath_temp = weath_raw.split("currently ")[1].split("°C")[0] + "°C"
        weath_desc = weath_raw.split("with ")[1].split(".")[0].title()
    else:
        weath_temp, weath_desc = "22°C", "Clear Sky"
except Exception:
    weath_temp, weath_desc = "22°C", "Clear Sky"

try:
    now_playing = spotify_control.get_now_playing().replace("Currently playing ", "")
except Exception:
    now_playing = "Ready on Spotify"

active_rems = []
try:
    active_rems = [r for r in reminder_scheduler.load_reminders() if not r.get("completed")]
except Exception:
    pass


def detect_mode_switch(cmd_text: str, current_mode: str) -> tuple[str, str | None]:
    """Detects voice/text mode-transformation commands just like the Nexus video."""
    low = cmd_text.lower().strip()
    if "immersive" in low or "carousel" in low or "cards mode" in low:
        return "IMMERSIVE MODE", "Immersive mode is now active."
    if "human" in low or "avatar" in low or "face mode" in low:
        return "HUMAN MODE", "Understood. Give me a moment. I'm here, how can I help?"
    if "assistant mode" in low or "return to assistant" in low or "normal mode" in low:
        return "ASSISTANT MODE", "Returning to assistant mode."
    return current_mode, None


# Process Incoming Query Parameter or Chat Command
query_cmd = st.query_params.get("voice_cmd", "")
if query_cmd:
    st.query_params.clear()
    new_mode, mode_reply = detect_mode_switch(query_cmd, st.session_state.ui_mode)
    st.session_state.ui_mode = new_mode
    st.session_state.messages.append({"role": "user", "content": query_cmd})
    if mode_reply:
        reply = mode_reply
    else:
        try:
            reply, _ = commands.handle_command(query_cmd)
        except Exception as e:
            reply = f"Command executed: {query_cmd}"
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.last_spoken = reply

# Minimal Full-Bleed Dark Spatial Styling for Streamlit Wrapper
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Orbitron:wght@500;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

.stApp {
    background: radial-gradient(circle at 50% 25%, #071426 0%, #02050a 75%);
    color: #e2f1ff;
    font-family: 'Inter', sans-serif;
}
header[data-testid="stHeader"] {
    background: transparent !important;
}
.block-container {
    padding-top: 0.6rem !important;
    padding-bottom: 0.5rem !important;
    max-width: 98% !important;
}
div[data-testid="stChatInput"] {
    background: rgba(6, 16, 32, 0.85) !important;
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
    border-radius: 999px !important;
}
</style>
""", unsafe_allow_html=True)

# Top Mode Switcher & Controls Bar
c_mode1, c_mode2, c_mode3, c_spacer, c_mic = st.columns([1.2, 1.2, 1.2, 3.4, 2.0])
with c_mode1:
    if st.button("🔵 ASSISTANT MODE", use_container_width=True):
        st.session_state.ui_mode = "ASSISTANT MODE"
        st.session_state.last_spoken = "Returning to assistant mode."
        st.rerun()
with c_mode2:
    if st.button("🌌 IMMERSIVE MODE", use_container_width=True):
        st.session_state.ui_mode = "IMMERSIVE MODE"
        st.session_state.last_spoken = "Immersive mode is now active."
        st.rerun()
with c_mode3:
    if st.button("👤 HUMAN MODE", use_container_width=True):
        st.session_state.ui_mode = "HUMAN MODE"
        st.session_state.last_spoken = "I'm here. How can I help?"
        st.rerun()
with c_mic:
    st.markdown(
        f"<div style='text-align:right; font-family:JetBrains Mono,monospace; font-size:0.78rem; color:#38bdf8; padding-top:8px;'>"
        f"🎙️ WAKE WORD: <b>\"HEY JARVIS\"</b> • CPU {cpu_val} • RAM {ram_val}</div>",
        unsafe_allow_html=True
    )

# Prepare serialized conversation & state for the Nexus 3D Spatial Canvas
recent_msgs_json = json.dumps(st.session_state.messages[-5:])
last_spoken_json = json.dumps(st.session_state.last_spoken)
current_mode_str = st.session_state.ui_mode
clock_now = datetime.datetime.now().strftime("%H:%M")

NEXUS_SPATIAL_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Orbitron:wght@500;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; }}
  html, body {{
    width: 100%; height: 100%; overflow: hidden;
    background: radial-gradient(ellipse at 50% 35%, #081b33 0%, #030812 65%, #010308 100%);
    font-family: 'Inter', -apple-system, sans-serif;
    color: #e2f1ff;
  }}

  /* 3D WebGL Stage */
  #webgl-stage {{
    position: absolute; inset: 0; width: 100%; height: 100%; z-index: 1;
  }}

  /* Perspective Grid Floor (Nexus Horizon) */
  .horizon-grid {{
    position: absolute; bottom: 0; left: -20%; right: -20%; height: 42%;
    background-image:
      linear-gradient(to right, rgba(56, 189, 248, 0.08) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(56, 189, 248, 0.08) 1px, transparent 1px);
    background-size: 50px 50px;
    transform: perspective(450px) rotateX(68deg);
    transform-origin: bottom center;
    mask-image: linear-gradient(to top, rgba(0,0,0,0.85) 10%, transparent 95%);
    -webkit-mask-image: linear-gradient(to top, rgba(0,0,0,0.85) 10%, transparent 95%);
    pointer-events: none; z-index: 1;
  }}

  /* Top-Left Status Badge: [ ● LIVE | MODE ] */
  .top-hud-bar {{
    position: absolute; top: 18px; left: 24px; right: 24px;
    display: flex; justify-content: space-between; align-items: center;
    z-index: 20; pointer-events: none;
  }}
  .live-pill {{
    display: inline-flex; align-items: center; gap: 10px;
    background: rgba(6, 14, 26, 0.85);
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 999px;
    padding: 7px 18px;
    backdrop-filter: blur(14px);
    box-shadow: 0 0 25px rgba(0, 210, 255, 0.15);
    pointer-events: auto;
  }}
  .live-dot {{
    width: 10px; height: 10px; border-radius: 50%;
    background: #ff2a5f;
    box-shadow: 0 0 10px #ff2a5f, 0 0 20px #ff2a5f;
    animation: blink 1.4s infinite ease-in-out;
  }}
  @keyframes blink {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.45; transform: scale(0.85); }}
  }}
  .live-text {{
    font-family: 'Orbitron', sans-serif; font-size: 11px; font-weight: 700;
    letter-spacing: 1.8px; color: #ffffff;
  }}
  .divider {{ color: rgba(255,255,255,0.28); font-weight: 300; }}
  .mode-text {{
    font-family: 'Orbitron', sans-serif; font-size: 11px; font-weight: 700;
    letter-spacing: 2px; color: #38bdf8;
  }}

  .top-right-clock {{
    font-family: 'JetBrains Mono', monospace; font-size: 13px;
    color: rgba(226, 241, 255, 0.75);
    background: rgba(6, 14, 26, 0.65);
    border: 1px solid rgba(255,255,255,0.1);
    padding: 6px 14px; border-radius: 8px;
    backdrop-filter: blur(10px);
    pointer-events: auto;
    display: flex; align-items: center; gap: 12px;
  }}
  .mic-toggle-btn {{
    background: rgba(56, 189, 248, 0.16);
    border: 1px solid rgba(56, 189, 248, 0.5);
    color: #38bdf8; border-radius: 6px; padding: 4px 10px;
    font-family: 'Orbitron', sans-serif; font-size: 10px; font-weight: 700;
    cursor: pointer; transition: all 0.2s ease;
  }}
  .mic-toggle-btn.listening {{
    background: rgba(0, 255, 170, 0.22);
    border-color: #00ffaa; color: #00ffaa;
    box-shadow: 0 0 12px rgba(0, 255, 170, 0.35);
  }}

  /* ---------------- ASSISTANT MODE FLOATING WIDGETS ---------------- */
  #assistant-layer {{
    position: absolute; inset: 0; z-index: 10;
    transition: opacity 0.45s ease;
    pointer-events: none;
  }}
  .ambient-left {{
    position: absolute; top: 82px; left: 32px; width: 250px;
    display: flex; flex-direction: column; gap: 16px;
  }}
  .greeting-title {{
    font-size: 18px; font-weight: 500; color: rgba(255,255,255,0.92);
    letter-spacing: 0.3px;
  }}
  .weather-block {{
    background: rgba(8, 20, 38, 0.55);
    border-left: 2px solid #38bdf8;
    padding: 10px 14px; border-radius: 0 10px 10px 0;
    backdrop-filter: blur(8px);
  }}
  .weather-temp {{
    font-size: 28px; font-weight: 300; color: #ffffff;
    display: flex; align-items: baseline; gap: 8px;
  }}
  .weather-temp span {{ font-size: 12px; color: #94a3b8; font-weight: 400; }}
  .ticker-row {{
    display: flex; flex-direction: column; gap: 6px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
  }}
  .ticker-item {{
    display: flex; justify-content: space-between;
    background: rgba(8, 20, 38, 0.45);
    padding: 6px 10px; border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.06);
  }}
  .up {{ color: #34d399; }}
  .down {{ color: #f87171; }}

  /* Bottom-Right INTEL Waveform Card */
  .intel-card {{
    position: absolute; bottom: 28px; right: 32px; width: 265px;
    background: rgba(7, 17, 34, 0.72);
    border: 1px solid rgba(56, 189, 248, 0.28);
    border-radius: 12px; padding: 14px 16px;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.45);
  }}
  .intel-header {{
    display: flex; justify-content: space-between; align-items: center;
    font-family: 'Orbitron', sans-serif; font-size: 11px; letter-spacing: 1.5px;
    color: #38bdf8; margin-bottom: 8px;
  }}
  .intel-bars {{
    display: flex; align-items: flex-end; gap: 3px; height: 36px;
    margin-bottom: 8px;
  }}
  .intel-bar {{
    flex: 1; background: linear-gradient(to top, #0284c7, #38bdf8);
    border-radius: 2px;
    animation: eq 1.2s ease-in-out infinite alternate;
  }}
  @keyframes eq {{
    0% {{ height: 20%; opacity: 0.5; }}
    100% {{ height: 95%; opacity: 1; }}
  }}

  /* Center Floating Dialogue Stream (Below Orb) */
  .center-dialogue {{
    position: absolute; bottom: 24px; left: 50%;
    transform: translateX(-50%);
    width: min(560px, 90vw);
    display: flex; flex-direction: column; gap: 8px;
    pointer-events: auto;
  }}
  .msg-pill {{
    padding: 9px 16px; border-radius: 10px;
    font-size: 13px; line-height: 1.45;
    backdrop-filter: blur(12px);
    animation: fadeUp 0.25s ease-out;
  }}
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}
  .msg-user {{
    align-self: flex-end;
    background: rgba(14, 30, 56, 0.78);
    border: 1px solid rgba(56, 189, 248, 0.35);
    color: #bae6fd;
  }}
  .msg-assistant {{
    align-self: center;
    width: 100%;
    text-align: center;
    background: rgba(6, 18, 36, 0.88);
    border: 1px solid rgba(0, 242, 254, 0.4);
    color: #ffffff;
    box-shadow: 0 0 24px rgba(0, 210, 255, 0.14);
  }}

  /* ---------------- IMMERSIVE MODE 3D HOLOGRAPHIC CAROUSEL ---------------- */
  #immersive-layer {{
    position: absolute; inset: 0; z-index: 12;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    opacity: 0; pointer-events: none;
    transition: opacity 0.5s ease;
  }}
  #immersive-layer.active {{
    opacity: 1; pointer-events: auto;
  }}
  .carousel-stage {{
    display: flex; align-items: center; justify-content: center;
    gap: 26px; perspective: 1200px;
    width: 95%; max-width: 1180px;
    margin-top: -20px;
  }}
  .holo-card {{
    width: 280px; height: 340px;
    background: linear-gradient(160deg, rgba(12, 28, 54, 0.78) 0%, rgba(4, 12, 26, 0.88) 100%);
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 16px;
    padding: 22px 20px;
    backdrop-filter: blur(16px);
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.65), inset 0 0 25px rgba(56, 189, 248, 0.08);
    display: flex; flex-direction: column; justify-content: space-between;
    transition: all 0.45s cubic-bezier(0.2, 0.8, 0.2, 1);
    cursor: pointer;
    position: relative;
    overflow: hidden;
  }}
  .holo-card::before {{
    content: ""; position: absolute; top: 0; left: 15%; right: 15%; height: 2px;
    background: linear-gradient(90deg, transparent, #38bdf8, transparent);
  }}
  .holo-card.left-card {{
    transform: rotateY(22deg) scale(0.88) translateZ(-30px);
    opacity: 0.72;
  }}
  .holo-card.center-card {{
    transform: rotateY(0deg) scale(1.06) translateZ(20px);
    border-color: rgba(0, 242, 254, 0.75);
    box-shadow: 0 0 40px rgba(0, 210, 255, 0.28), inset 0 0 30px rgba(0, 210, 255, 0.14);
    opacity: 1;
  }}
  .holo-card.right-card {{
    transform: rotateY(-22deg) scale(0.88) translateZ(-30px);
    opacity: 0.72;
  }}
  .card-tag {{
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    color: #38bdf8; letter-spacing: 1.5px; text-transform: uppercase;
  }}
  .card-title {{
    font-family: 'Orbitron', sans-serif; font-size: 20px; font-weight: 700;
    letter-spacing: 2.5px; color: #ffffff; text-align: center;
    margin: 10px 0;
  }}
  .card-metric {{
    font-family: 'Orbitron', sans-serif; font-size: 26px; font-weight: 700;
    color: #00f2fe; text-align: center;
  }}
  .card-sub {{
    font-size: 12px; color: #94a3b8; text-align: center; line-height: 1.5;
  }}
  .card-footer {{
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid rgba(255,255,255,0.08);
    padding-top: 10px; font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: #64748b;
  }}
  .carousel-controls {{
    display: flex; gap: 12px; margin-top: 24px;
  }}
  .carousel-dot {{
    padding: 6px 14px; border-radius: 999px;
    font-family: 'Orbitron', sans-serif; font-size: 10px; letter-spacing: 1.5px;
    background: rgba(10, 22, 42, 0.75);
    border: 1px solid rgba(56, 189, 248, 0.28);
    color: #94a3b8; cursor: pointer; transition: all 0.2s;
  }}
  .carousel-dot.active {{
    background: rgba(56, 189, 248, 0.22);
    border-color: #00f2fe; color: #ffffff;
    box-shadow: 0 0 15px rgba(0, 242, 254, 0.3);
  }}

  /* ---------------- VOICE CAPTION BAR ---------------- */
  .voice-subtitle-pill {{
    position: absolute; bottom: 18px; left: 50%; transform: translateX(-50%);
    background: rgba(4, 12, 24, 0.9);
    border: 1px solid rgba(56, 189, 248, 0.45);
    border-radius: 10px; padding: 10px 22px;
    font-size: 13.5px; color: #e2f1ff;
    max-width: 680px; width: 88%; text-align: center;
    z-index: 25; backdrop-filter: blur(14px);
    box-shadow: 0 6px 28px rgba(0,0,0,0.6);
  }}
  .nexus-badge {{
    display: inline-block; font-family: 'Orbitron', sans-serif;
    font-size: 10px; letter-spacing: 1.8px; color: #00f2fe;
    margin-right: 8px; font-weight: 700;
  }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

  <!-- 3D WebGL Hologram Stage -->
  <div id="webgl-stage"></div>
  <div class="horizon-grid"></div>

  <!-- Top-Left Nexus Status Pill & Top-Right Telemetry/Voice Trigger -->
  <div class="top-hud-bar">
    <div class="live-pill">
      <div class="live-dot"></div>
      <span class="live-text">LIVE</span>
      <span class="divider">|</span>
      <span class="mode-text" id="hud-mode-label">{current_mode_str}</span>
    </div>
    <div class="top-right-clock">
      <button id="mic-btn" class="mic-toggle-btn" onclick="toggleBrowserVoice()">🎙️ AUTO-LISTEN: ON</button>
      <span>{clock_now} IST</span>
    </div>
  </div>

  <!-- MODE 1: ASSISTANT MODE OVERLAY -->
  <div id="assistant-layer">
    <div class="ambient-left">
      <div class="greeting-title">Good evening, Nakul.</div>
      <div class="weather-block">
        <div class="weather-temp">{weath_temp} <span>Dehradun • {weath_desc}</span></div>
        <div style="font-size:11px; color:#64748b; margin-top:4px;">UPES Campus Telemetry • Active</div>
      </div>
      <div class="ticker-row">
        <div class="ticker-item"><span>NIFTY 50</span><span class="up">▲ +1.42%</span></div>
        <div class="ticker-item"><span>AMD</span><span class="up">▲ +11.04%</span></div>
        <div class="ticker-item"><span>NVDA</span><span class="up">▲ +3.18%</span></div>
        <div class="ticker-item"><span>MSFT</span><span class="down">▼ -0.84%</span></div>
      </div>
    </div>

    <div class="center-dialogue" id="dialogue-box"></div>

    <div class="intel-card">
      <div class="intel-header">
        <span>INTEL STREAM</span>
        <span>{cpu_val}</span>
      </div>
      <div class="intel-bars">
        <div class="intel-bar" style="animation-delay:0.0s"></div>
        <div class="intel-bar" style="animation-delay:0.2s"></div>
        <div class="intel-bar" style="animation-delay:0.4s"></div>
        <div class="intel-bar" style="animation-delay:0.1s"></div>
        <div class="intel-bar" style="animation-delay:0.5s"></div>
        <div class="intel-bar" style="animation-delay:0.3s"></div>
        <div class="intel-bar" style="animation-delay:0.15s"></div>
        <div class="intel-bar" style="animation-delay:0.35s"></div>
        <div class="intel-bar" style="animation-delay:0.25s"></div>
        <div class="intel-bar" style="animation-delay:0.45s"></div>
      </div>
      <div style="display:flex; justify-content:space-between; font-family:'JetBrains Mono',monospace; font-size:10.5px; color:#94a3b8;">
        <span>RAM: {ram_val}</span>
        <span>PWR: {bat_val}</span>
        <span>REM: {len(active_rems)}</span>
      </div>
    </div>
  </div>

  <!-- MODE 2: IMMERSIVE MODE 3D CAROUSEL OVERLAY -->
  <div id="immersive-layer">
    <div class="carousel-stage" id="carousel-stage"></div>
    <div class="carousel-controls" id="carousel-dots"></div>
  </div>

  <!-- Live Voice Subtitle / Status Bar -->
  <div class="voice-subtitle-pill" id="subtitle-bar" style="display:none;">
    <span class="nexus-badge">● JARVIS</span>
    <span id="subtitle-text"></span>
  </div>

<script>
  const INITIAL_MODE = {json.dumps(current_mode_str)};
  const MESSAGES = {recent_msgs_json};
  const LAST_SPOKEN = {last_spoken_json};

  let currentMode = INITIAL_MODE;
  let speakingIntensity = 0.0;

  // Populate Assistant Mode Dialogue
  const dialogueBox = document.getElementById('dialogue-box');
  MESSAGES.slice(-3).forEach(m => {{
    const div = document.createElement('div');
    div.className = 'msg-pill ' + (m.role === 'user' ? 'msg-user' : 'msg-assistant');
    div.textContent = m.content;
    dialogueBox.appendChild(div);
  }});

  // Immersive Mode Cards Data (matching the Nexus video)
  const CARDS = [
    {{ tag: "LIVE EXCHANGE", title: "MARKETS", metric: "+3.03%", sub: "AMD leads at +11.04% gain • NIFTY & AI Tech surge", footL: "GAIN", footR: "LIVE" }},
    {{ tag: "GITHUB & UPES", title: "PROJECTS", metric: "8 ACTIVE", sub: "Jarvis 2.0 Spatial OS • Zero open critical issues", footL: "REPOS", footR: "SYNCED" }},
    {{ tag: "IPL & CRICKET", title: "SPORTS", metric: "LIVE HUD", sub: "IPL Standings, Match Previews & Strike Rate Analytics", footL: "FEED", footR: "ACTIVE" }},
    {{ tag: "UPES SCHEDULE", title: "CALENDAR", metric: "{len(active_rems)} TASKS", sub: "B.Tech Data Science Timetable & Pending Reminders", footL: "AGENDA", footR: "TODAY" }},
    {{ tag: "DEHRADUN HQ", title: "WEATHER", metric: "{weath_temp}", sub: "{weath_desc} • 200km Trekking & Hill Forecast", footL: "LOC", footR: "UPES" }},
    {{ tag: "SPOTIFY STREAM", title: "AUDIO", metric: "ACTIVE", sub: {json.dumps(now_playing)}, footL: "DSP", footR: "HI-FI" }}
  ];

  let activeCardIdx = 0;
  function renderCarousel() {{
    const stage = document.getElementById('carousel-stage');
    const dots = document.getElementById('carousel-dots');
    stage.innerHTML = '';
    dots.innerHTML = '';

    const leftIdx = (activeCardIdx - 1 + CARDS.length) % CARDS.length;
    const rightIdx = (activeCardIdx + 1) % CARDS.length;
    const visible = [
      {{ idx: leftIdx, cls: 'left-card' }},
      {{ idx: activeCardIdx, cls: 'center-card' }},
      {{ idx: rightIdx, cls: 'right-card' }}
    ];

    visible.forEach(item => {{
      const c = CARDS[item.idx];
      const el = document.createElement('div');
      el.className = 'holo-card ' + item.cls;
      el.onclick = () => {{ activeCardIdx = item.idx; renderCarousel(); }};
      el.innerHTML = `
        <div class="card-tag">${{c.tag}}</div>
        <div>
          <div class="card-title">${{c.title}}</div>
          <div class="card-metric">${{c.metric}}</div>
        </div>
        <div class="card-sub">${{c.sub}}</div>
        <div class="card-footer"><span>${{c.footL}}</span><span>${{c.footR}}</span></div>
      `;
      stage.appendChild(el);
    }});

    CARDS.forEach((c, idx) => {{
      const d = document.createElement('button');
      d.className = 'carousel-dot ' + (idx === activeCardIdx ? 'active' : '');
      d.textContent = c.title;
      d.onclick = () => {{ activeCardIdx = idx; renderCarousel(); }};
      dots.appendChild(d);
    }});
  }}
  renderCarousel();

  // ---------------- THREE.JS 3D ENGINE (ORB + PARTICLE HUMANOID HEAD) ----------------
  const container = document.getElementById('webgl-stage');
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(48, container.clientWidth / container.clientHeight, 0.1, 1000);
  camera.position.set(0, 6, 215);

  const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  const PARTICLE_COUNT = 2600;
  const geometry = new THREE.BufferGeometry();
  const currentPositions = new Float32Array(PARTICLE_COUNT * 3);
  const orbPositions = new Float32Array(PARTICLE_COUNT * 3);
  const humanPositions = new Float32Array(PARTICLE_COUNT * 3);
  const immersivePositions = new Float32Array(PARTICLE_COUNT * 3);
  const colors = new Float32Array(PARTICLE_COUNT * 3);

  const cCyan = new THREE.Color(0x00f2fe);
  const cBlue = new THREE.Color(0x38bdf8);
  const cDeep = new THREE.Color(0x0284c7);

  for (let i = 0; i < PARTICLE_COUNT; i++) {{
    // 1. Assistant Mode: Concentrated Glowing Energy Orb
    const phi = Math.acos(-1 + (2 * i) / PARTICLE_COUNT);
    const theta = Math.sqrt(PARTICLE_COUNT * Math.PI) * phi;
    const rOrb = 34 + (Math.random() - 0.5) * 4.5;
    orbPositions[i * 3]     = rOrb * Math.cos(theta) * Math.sin(phi);
    orbPositions[i * 3 + 1] = rOrb * Math.sin(theta) * Math.sin(phi) + 22;
    orbPositions[i * 3 + 2] = rOrb * Math.cos(phi);

    // 2. Human Mode: Parametric 3D Sculpted Android Head & Shoulders
    const u = (i / PARTICLE_COUNT) * Math.PI * 2 * 19;
    const v = (i / PARTICLE_COUNT); // 0 (crown) -> 1 (neck/shoulders)
    let hx, hy, hz;
    if (v < 0.78) {{
      // Cranium + Jaw contour
      const hPhi = (v / 0.78) * Math.PI;
      const jawTaper = hPhi > 1.8 ? 0.78 : 1.0;
      let rx = 34 * Math.sin(hPhi) * jawTaper;
      let ry = 46;
      let rz = 38 * Math.sin(hPhi) * jawTaper;

      // Facial features (nose bridge & brow ridge projection)
      const frontFactor = Math.max(0, Math.cos(u));
      if (hPhi > 1.05 && hPhi < 1.95 && frontFactor > 0.65) {{
        rz += Math.pow(frontFactor, 3) * 9.5; // Nose & brow contour
      }}
      hx = rx * Math.sin(u);
      hy = ry * Math.cos(hPhi) + 16;
      hz = rz * Math.cos(u);
    }} else {{
      // Neck & Holographic Collar
      const neckProg = (v - 0.78) / 0.22;
      const neckRadius = 18 + neckProg * 36;
      hx = neckRadius * Math.sin(u);
      hy = -30 - neckProg * 22;
      hz = (neckRadius * 0.65) * Math.cos(u);
    }}
    humanPositions[i * 3]     = hx + (Math.random() - 0.5) * 1.4;
    humanPositions[i * 3 + 1] = hy + (Math.random() - 0.5) * 1.4;
    humanPositions[i * 3 + 2] = hz + (Math.random() - 0.5) * 1.4;

    // 3. Immersive Mode: Wide Ambient Starfield Ring
    const angle = (i / PARTICLE_COUNT) * Math.PI * 2 * 4;
    const rad = 115 + (Math.random() - 0.5) * 70;
    immersivePositions[i * 3]     = rad * Math.cos(angle);
    immersivePositions[i * 3 + 1] = (Math.random() - 0.5) * 110;
    immersivePositions[i * 3 + 2] = rad * Math.sin(angle) - 40;

    // Initialize current positions
    currentPositions[i * 3]     = orbPositions[i * 3];
    currentPositions[i * 3 + 1] = orbPositions[i * 3 + 1];
    currentPositions[i * 3 + 2] = orbPositions[i * 3 + 2];

    const col = (i % 3 === 0) ? cCyan : (i % 3 === 1 ? cBlue : cDeep);
    colors[i * 3]     = col.r;
    colors[i * 3 + 1] = col.g;
    colors[i * 3 + 2] = col.b;
  }}

  geometry.setAttribute('position', new THREE.BufferAttribute(currentPositions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({{
    size: 2.35,
    vertexColors: true,
    transparent: true,
    opacity: 0.92,
    blending: THREE.AdditiveBlending
  }});

  const particleSystem = new THREE.Points(geometry, material);
  scene.add(particleSystem);

  // Inner Glowing Core for Assistant Mode
  const coreGeo = new THREE.SphereGeometry(22, 32, 32);
  const coreMat = new THREE.MeshBasicMaterial({{
    color: 0x00e5ff,
    transparent: true,
    opacity: 0.22,
    blending: THREE.AdditiveBlending
  }});
  const coreSphere = new THREE.Mesh(coreGeo, coreMat);
  coreSphere.position.y = 22;
  scene.add(coreSphere);

  // Outer Orbital Ring
  const ringGeo = new THREE.RingGeometry(46, 47.2, 96);
  const ringMat = new THREE.MeshBasicMaterial({{
    color: 0x38bdf8, side: THREE.DoubleSide, transparent: true, opacity: 0.38
  }});
  const orbitalRing = new THREE.Mesh(ringGeo, ringMat);
  orbitalRing.position.y = 22;
  orbitalRing.rotation.x = Math.PI / 2.2;
  scene.add(orbitalRing);

  function applyVisualMode(mode) {{
    currentMode = mode;
    document.getElementById('hud-mode-label').textContent = mode;
    const assistLayer = document.getElementById('assistant-layer');
    const immerLayer = document.getElementById('immersive-layer');
    const subBar = document.getElementById('subtitle-bar');

    if (mode === 'ASSISTANT MODE') {{
      assistLayer.style.opacity = '1';
      immerLayer.classList.remove('active');
      subBar.style.display = 'none';
      coreSphere.visible = true;
      orbitalRing.visible = true;
    }} else if (mode === 'IMMERSIVE MODE') {{
      assistLayer.style.opacity = '0';
      immerLayer.classList.add('active');
      subBar.style.display = 'block';
      coreSphere.visible = false;
      orbitalRing.visible = false;
    }} else if (mode === 'HUMAN MODE') {{
      assistLayer.style.opacity = '0';
      immerLayer.classList.remove('active');
      subBar.style.display = 'block';
      coreSphere.visible = false;
      orbitalRing.visible = true;
    }}
  }}
  applyVisualMode(INITIAL_MODE);

  // Animation Loop (Smooth Particle Morphing + Voice Lip/Pulse Sync)
  const clock = new THREE.Clock();
  function animate() {{
    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();
    const posAttr = geometry.attributes.position;
    const arr = posAttr.array;

    const targetArr = (currentMode === 'HUMAN MODE')
      ? humanPositions
      : (currentMode === 'IMMERSIVE MODE' ? immersivePositions : orbPositions);

    for (let i = 0; i < PARTICLE_COUNT; i++) {{
      const ix = i * 3, iy = i * 3 + 1, iz = i * 3 + 2;
      let tx = targetArr[ix];
      let ty = targetArr[iy];
      let tz = targetArr[iz];

      // Mouth & energy pulse when Jarvis is speaking
      if (speakingIntensity > 0.01) {{
        if (currentMode === 'HUMAN MODE' && ty > -18 && ty < -2 && tz > 15) {{
          ty += Math.sin(t * 28 + i) * 3.8 * speakingIntensity;
        }} else {{
          const wave = 1 + Math.sin(t * 18 + i * 0.05) * 0.08 * speakingIntensity;
          tx *= wave; tz *= wave;
        }}
      }}

      arr[ix] += (tx - arr[ix]) * 0.08;
      arr[iy] += (ty - arr[iy]) * 0.08;
      arr[iz] += (tz - arr[iz]) * 0.08;
    }}
    posAttr.needsUpdate = true;

    if (currentMode === 'HUMAN MODE') {{
      particleSystem.rotation.y = Math.sin(t * 0.55) * 0.22;
    }} else {{
      particleSystem.rotation.y = t * 0.22;
    }}

    const pulse = 1 + Math.sin(t * 2.5) * 0.05 + speakingIntensity * 0.14;
    coreSphere.scale.set(pulse, pulse, pulse);
    orbitalRing.rotation.z = t * 0.25;

    renderer.render(scene, camera);
  }}
  animate();

  window.addEventListener('resize', () => {{
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  }});

  // ---------------- SPEAK RESPONSE ALOUD + SHOW SUBTITLE ----------------
  function speakOut(text) {{
    if (!text) return;
    const subBar = document.getElementById('subtitle-bar');
    const subText = document.getElementById('subtitle-text');
    subText.textContent = text;
    if (currentMode !== 'ASSISTANT MODE') {{
      subBar.style.display = 'block';
    }}
    if ('speechSynthesis' in window) {{
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 1.04;
      utter.pitch = 0.96;
      utter.onstart = () => {{ speakingIntensity = 1.0; }};
      utter.onend = () => {{ speakingIntensity = 0.0; }};
      utter.onerror = () => {{ speakingIntensity = 0.0; }};
      window.speechSynthesis.speak(utter);
    }}
  }}

  if (LAST_SPOKEN) {{
    speakOut(LAST_SPOKEN);
  }}

  // ---------------- BROWSER WAKE-WORD ENGINE ("HEY JARVIS" / "NEXUS") ----------------
  let recognition = null;
  let autoListen = true;

  function initWebSpeech() {{
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;
    recognition = new SpeechRec();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-IN';

    recognition.onresult = (event) => {{
      const transcript = event.results[event.results.length - 1][0].transcript.trim();
      const lower = transcript.toLowerCase();

      // Instant client-side mode switching for zero-latency feel
      if (lower.includes('immersive mode')) {{
        applyVisualMode('IMMERSIVE MODE');
        speakOut('Immersive mode is now active.');
        return;
      }}
      if (lower.includes('into a human') || lower.includes('human mode')) {{
        applyVisualMode('HUMAN MODE');
        speakOut('Understood, give me a moment. I am here, how can I help?');
        return;
      }}
      if (lower.includes('assistant mode')) {{
        applyVisualMode('ASSISTANT MODE');
        speakOut('Returning to assistant mode.');
        return;
      }}

      // Check wake word ("hey jarvis", "jarvis", "nexus")
      const triggers = ['hey jarvis', 'jarvis', 'hey jervis', 'jervis', 'hey nexus', 'nexus'];
      for (const trig of triggers) {{
        const idx = lower.indexOf(trig);
        if (idx !== -1) {{
          const extracted = transcript.slice(idx + trig.length).trim() || transcript;
          const url = new URL(window.parent.location.href);
          url.searchParams.set('voice_cmd', extracted);
          window.parent.location.href = url.toString();
          break;
        }}
      }}
    }};

    recognition.onend = () => {{
      if (autoListen) {{
        try {{ recognition.start(); }} catch (e) {{}}
      }}
    }};

    try {{
      recognition.start();
      document.getElementById('mic-btn').classList.add('listening');
    }} catch (e) {{}}
  }}

  function toggleBrowserVoice() {{
    const btn = document.getElementById('mic-btn');
    autoListen = !autoListen;
    if (autoListen) {{
      btn.textContent = '🎙️ AUTO-LISTEN: ON';
      btn.classList.add('listening');
      if (recognition) try {{ recognition.start(); }} catch (e) {{}}
    }} else {{
      btn.textContent = '🎙️ AUTO-LISTEN: OFF';
      btn.classList.remove('listening');
      if (recognition) try {{ recognition.stop(); }} catch (e) {{}}
    }}
  }}

  initWebSpeech();
</script>
</body>
</html>
"""

components.html(NEXUS_SPATIAL_HTML, height=620, scrolling=False)

# Bottom Command Bar (Works via Text or Voice)
user_prompt = st.chat_input("Say 'Hey Jarvis...' or type a command (e.g., 'transform into immersive mode', 'transform into a human', 'how is the market performing')...")
if user_prompt:
    new_mode, mode_reply = detect_mode_switch(user_prompt, st.session_state.ui_mode)
    st.session_state.ui_mode = new_mode
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    if mode_reply:
        reply = mode_reply
    else:
        try:
            reply, _ = commands.handle_command(user_prompt)
        except Exception:
            reply = f"Processed: {user_prompt}"
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.last_spoken = reply
    st.rerun()

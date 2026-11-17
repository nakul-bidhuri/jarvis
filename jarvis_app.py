"""
jarvis_app.py — Jarvis 2.0 AI Spatial OS & Holographic Voice Control Center.

Inspired by Nexus Spatial OS and Iron Man's JARVIS:
  - 🌐 5 Dynamic Spatial Environments (Command Center, Dark Lab, Cyber Glass, Observatory Ocean, Minimal Studio)
  - ✨ Interactive 3D Holographic Particle Core & Cyber Avatar Embodiment Mode (30 FPS)
  - 🔊 Studio-Quality Synthesized Acoustic Feedback Cues (Sine wave chirps & chords)
  - 📊 Real-Time Live Telemetry HUD: CPU, RAM, Battery, and Live Dehradun Weather
  - ⏰ Autonomous Reminders & Schedule Board (Real-time updates & acoustic alarms)
  - 🎵 Spotify Media Player Controller (Zero YouTube lag, seamless background playback)
  - 💬 Live Conversation Transcript with High-Speed Gemini 3.5 Flash Lite & Fast Router
  - 🎙️ Push-To-Talk [LISTEN NOW] Button + Voice Wake Detection ("Jarvis", "Hey Jervis")
"""

import threading
import time
import datetime
import math
import random
import os
import psutil
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

import memory_manager
import commands
import voice_engine as voice
import music_player
import spotify_control
import audio_cues
import live_knowledge
import reminder_scheduler
import daily_briefing
import safe_messaging
import laptop_controller

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ==================== SPATIAL ENVIRONMENT THEMES ====================
SPATIAL_THEMES = {
    "🌐 Command Center": {
        "bg": "#060913", "card": "#0D1527", "card_inner": "#09101F",
        "accent": "#00FFCC", "accent_alt": "#00E5FF", "text": "#ECEFF1", "sub": "#78909C",
        "canvas_bg": "#060913", "pill_bg": "#09221C",
        "particles": ["#00FFCC", "#00E5FF", "#38BDF8", "#0284C7", "#7DD3FC"]
    },
    "🧪 Dark Laboratory": {
        "bg": "#050B08", "card": "#0C1710", "card_inner": "#08100B",
        "accent": "#00E676", "accent_alt": "#69F0AE", "text": "#E8F5E9", "sub": "#81C784",
        "canvas_bg": "#050B08", "pill_bg": "#0A2416",
        "particles": ["#00E676", "#69F0AE", "#B9F6CA", "#00C853", "#A7F3D0"]
    },
    "🔮 Cyber Glass": {
        "bg": "#0D0818", "card": "#18102C", "card_inner": "#120B22",
        "accent": "#EA80FC", "accent_alt": "#B388FF", "text": "#F3E5F5", "sub": "#CE93D8",
        "canvas_bg": "#0D0818", "pill_bg": "#2A103D",
        "particles": ["#EA80FC", "#B388FF", "#D500F9", "#7C4DFF", "#F0ABFC"]
    },
    "🌊 Observatory Ocean": {
        "bg": "#030B14", "card": "#081626", "card_inner": "#05101C",
        "accent": "#00E5FF", "accent_alt": "#40C4FF", "text": "#E0F7FA", "sub": "#80DEEA",
        "canvas_bg": "#030B14", "pill_bg": "#052233",
        "particles": ["#00E5FF", "#40C4FF", "#00B0FF", "#0288D1", "#BAE6FD"]
    },
    "🏛️ Minimal Studio": {
        "bg": "#0C0C0F", "card": "#16161C", "card_inner": "#111116",
        "accent": "#ECEFF1", "accent_alt": "#CFD8DC", "text": "#FFFFFF", "sub": "#90A4AE",
        "canvas_bg": "#0C0C0F", "pill_bg": "#22222B",
        "particles": ["#FFFFFF", "#ECEFF1", "#CFD8DC", "#B0BEC5", "#E2E8F0"]
    }
}

def _generate_fibonacci_sphere(n_points=110):
    """Generates evenly spaced 3D points on a unit sphere using the Fibonacci spiral."""
    points = []
    phi = math.pi * (math.sqrt(5.0) - 1.0)
    for i in range(n_points):
        y = 1 - (i / float(n_points - 1)) * 2
        radius_at_y = math.sqrt(max(0.0, 1.0 - y * y))
        theta = phi * i
        x = math.cos(theta) * radius_at_y
        z = math.sin(theta) * radius_at_y
        points.append((x, y, z))
    return points

_SPHERE_POINTS = _generate_fibonacci_sphere(110)


class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JARVIS 2.0 — Spatial AI Operating System")
        self.geometry("1160x780")
        self.minsize(1020, 700)

        # State Variables
        self.current_theme_name = "🌐 Command Center"
        self.theme = SPATIAL_THEMES[self.current_theme_name]
        self.visual_mode = "SPHERE"  # 'SPHERE' or 'AVATAR'
        self.configure(fg_color=self.theme["bg"])

        self.is_assistant_running = True
        self.is_session_active = False  # False = Cold Sleep (needs 'Hey Jarvis'); True = Active (needs only 'Jarvis')
        self.assistant_state = "IDLE"  # STOPPED, IDLE, LISTENING, THINKING, SPEAKING
        self.assistant_busy = False
        self.voice_thread = None
        self.animation_phase = 0.0

        # Shortcut Key Controller (Ctrl + Alt + J)
        self._hotkey_event = threading.Event()
        self._last_hotkey_time = 0.0
        self._register_global_hotkey()

        # Build Full Spatial HUD Layout
        self._setup_layout()
        self._animate_ai_core()
        self.refresh_brain_view()
        self.refresh_reminders_view()

        # Wire reminders scheduler update callback
        reminder_scheduler.set_reminder_callback(lambda: self.safe_after(0, self.refresh_reminders_view))

        self.log_transcript(
            "SYSTEM",
            "⚡ Jarvis 2.0 Spatial OS Initialized.\n"
            "• Acoustic Feedback: Active\n"
            "• Speech Engine: Local Whisper (CPU int8)\n"
            "• Shortcut Key: Press [Ctrl + Alt + J] to start or close Jarvis anytime!",
            self.theme["accent"]
        )

        # Start background threads for telemetry and voice
        self.after(200, self._start_voice_thread)
        self.after(500, self._periodic_telemetry_loop)

    def safe_after(self, delay_ms: int, callback):
        """Thread-safe UI scheduling that never raises RuntimeError."""
        try:
            if self.winfo_exists():
                self.after(delay_ms, callback)
        except Exception:
            pass

    def _start_voice_thread(self):
        if not self.voice_thread or not self.voice_thread.is_alive():
            self.voice_thread = threading.Thread(target=self._run_conversational_loop, daemon=True)
            self.voice_thread.start()

    def _setup_layout(self):
        self.grid_columnconfigure(0, weight=3) # Left: 3D Hologram Stage + Conversation Box
        self.grid_columnconfigure(1, weight=2) # Right: Live Widgets & Knowledge HUD
        self.grid_rowconfigure(1, weight=1)

        t = self.theme

        # ==================== TOP NAVIGATION BAR ====================
        self.top_bar = ctk.CTkFrame(self, height=72, corner_radius=0, fg_color=t["card"])
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.top_bar.grid_columnconfigure(4, weight=1)

        self.logo_lbl = ctk.CTkLabel(
            self.top_bar, 
            text="⚡ JARVIS 2.0", 
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color=t["accent"]
        )
        self.logo_lbl.grid(row=0, column=0, padx=(18, 10), pady=16, sticky="w")

        # Primary Push-to-Talk LISTEN NOW Button
        self.btn_listen = ctk.CTkButton(
            self.top_bar,
            text="🎙️ LISTEN NOW",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#00C853",
            hover_color="#009624",
            width=135,
            height=36,
            corner_radius=8,
            command=self.trigger_direct_listen
        )
        self.btn_listen.grid(row=0, column=1, padx=6, pady=16)

        # Spatial Environment Selector
        self.theme_menu = ctk.CTkOptionMenu(
            self.top_bar,
            values=list(SPATIAL_THEMES.keys()),
            font=ctk.CTkFont(size=11),
            width=165,
            fg_color=t["card_inner"],
            button_color=t["card_inner"],
            command=self._on_theme_change
        )
        self.theme_menu.set(self.current_theme_name)
        self.theme_menu.grid(row=0, column=2, padx=6, pady=16)

        # Visual Mode Toggle (Sphere vs Avatar)
        self.btn_mode_toggle = ctk.CTkButton(
            self.top_bar,
            text="✨ 3D Orb",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=t["card_inner"],
            hover_color="#2D1A45",
            width=90,
            height=34,
            command=self._toggle_visual_mode
        )
        self.btn_mode_toggle.grid(row=0, column=3, padx=6, pady=16)

        # Status Pill
        self.header_status = ctk.CTkLabel(
            self.top_bar,
            text="● ONLINE — READY",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=t["accent"],
            fg_color=t["pill_bg"],
            corner_radius=12,
            padx=14,
            pady=5
        )
        self.header_status.grid(row=0, column=4, padx=10, pady=16, sticky="w")

        # Stop Speech / Interrupt button
        self.btn_interrupt = ctk.CTkButton(
            self.top_bar,
            text="🛑 Stop Speech",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#37474F",
            hover_color="#D50000",
            width=105,
            height=34,
            command=self._interrupt_speech
        )
        self.btn_interrupt.grid(row=0, column=5, padx=6, pady=16)

        # Mic Active / Pause toggle button
        self.btn_talk_toggle = ctk.CTkButton(
            self.top_bar,
            text="🟢 MIC ACTIVE",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#004D40",
            hover_color="#00241B",
            width=115,
            height=34,
            command=self.toggle_voice_session
        )
        self.btn_talk_toggle.grid(row=0, column=6, padx=(6, 16), pady=16)

        # ==================== LEFT PANE: 3D CORE & LIVE DIALOGUE ====================
        self.left_pane = ctk.CTkFrame(self, fg_color=t["card"], corner_radius=14)
        self.left_pane.grid(row=1, column=0, sticky="nsew", padx=(14, 8), pady=(12, 12))
        self.left_pane.grid_columnconfigure(0, weight=1)
        self.left_pane.grid_rowconfigure(2, weight=1)

        # Central 3D Spatial Canvas Stage
        self.canvas = tk.Canvas(
            self.left_pane,
            width=280,
            height=190,
            bg=t["canvas_bg"],
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, pady=(10, 2))

        # Dynamic State Guidance Banner
        self.banner_state = ctk.CTkLabel(
            self.left_pane,
            text="🟢 READY — PRESS [Ctrl + Alt + J] OR CLICK [LISTEN NOW] TO START",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=t["accent"],
            fg_color=t["card_inner"],
            corner_radius=10,
            padx=16,
            pady=7
        )
        self.banner_state.grid(row=1, column=0, padx=16, pady=(0, 6))

        # Live Conversation Transcript Box
        self.transcript_box = ctk.CTkTextbox(
            self.left_pane,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=t["card_inner"],
            text_color=t["text"],
            corner_radius=8,
            wrap="word"
        )
        self.transcript_box.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 8))

        # Bottom Input Bar
        self.cmd_bar = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        self.cmd_bar.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.cmd_bar.grid_columnconfigure(0, weight=1)

        self.cmd_entry = ctk.CTkEntry(
            self.cmd_bar,
            placeholder_text="Ask anything or command (e.g. 'brief me', 'weather', 'play Believer', 'remind me at 6 PM to call Rahul')...",
            font=ctk.CTkFont(size=12),
            height=38,
            fg_color=t["card_inner"],
            border_color="#1E293B"
        )
        self.cmd_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.cmd_entry.bind("<Return>", lambda event: self.send_text_command())

        self.btn_send = ctk.CTkButton(
            self.cmd_bar,
            text="Send",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=75,
            height=38,
            fg_color="#6200EA",
            hover_color="#7C4DFF",
            command=self.send_text_command
        )
        self.btn_send.grid(row=0, column=1)

        # ==================== RIGHT PANE: LIVE TELEMETRY & KNOWLEDGE HUD ====================
        self.right_pane = ctk.CTkFrame(self, fg_color=t["card"], corner_radius=14)
        self.right_pane.grid(row=1, column=1, sticky="nsew", padx=(6, 14), pady=(12, 12))
        self.right_pane.grid_columnconfigure(0, weight=1)
        self.right_pane.grid_rowconfigure(2, weight=1)

        # 1. Telemetry Bar (Live Battery %, CPU %, RAM %, Weather)
        self.telemetry_card = ctk.CTkFrame(self.right_pane, fg_color=t["card_inner"], corner_radius=10)
        self.telemetry_card.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        self.telemetry_card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.lbl_cpu = ctk.CTkLabel(self.telemetry_card, text="CPU: 0%", font=ctk.CTkFont(size=11, weight="bold"), text_color=t["accent_alt"])
        self.lbl_cpu.grid(row=0, column=0, padx=6, pady=6)

        self.lbl_ram = ctk.CTkLabel(self.telemetry_card, text="RAM: 0%", font=ctk.CTkFont(size=11, weight="bold"), text_color=t["accent"])
        self.lbl_ram.grid(row=0, column=1, padx=6, pady=6)

        self.lbl_bat = ctk.CTkLabel(self.telemetry_card, text="BAT: --%", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FFD54F")
        self.lbl_bat.grid(row=0, column=2, padx=6, pady=6)

        self.lbl_weather = ctk.CTkLabel(self.telemetry_card, text="🌦️ Dehradun: 22°C", font=ctk.CTkFont(size=11, weight="bold"), text_color="#80DEEA")
        self.lbl_weather.grid(row=0, column=3, padx=6, pady=6)

        # 2. Metric Stats Card (Facts, Notes, Reminders)
        self.metric_card = ctk.CTkFrame(self.right_pane, fg_color=t["card_inner"], corner_radius=10)
        self.metric_card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
        self.metric_card.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_facts_num = ctk.CTkLabel(self.metric_card, text="0", font=ctk.CTkFont(size=17, weight="bold"), text_color=t["accent_alt"])
        self.lbl_facts_num.grid(row=0, column=0, pady=(4, 0))
        ctk.CTkLabel(self.metric_card, text="Learned Facts", font=ctk.CTkFont(size=10), text_color=t["sub"]).grid(row=1, column=0, pady=(0, 4))

        self.lbl_reminders_num = ctk.CTkLabel(self.metric_card, text="0", font=ctk.CTkFont(size=17, weight="bold"), text_color="#FFD54F")
        self.lbl_reminders_num.grid(row=0, column=1, pady=(4, 0))
        ctk.CTkLabel(self.metric_card, text="Active Reminders", font=ctk.CTkFont(size=10), text_color=t["sub"]).grid(row=1, column=1, pady=(0, 4))

        self.lbl_notes_num = ctk.CTkLabel(self.metric_card, text="0", font=ctk.CTkFont(size=17, weight="bold"), text_color="#B388FF")
        self.lbl_notes_num.grid(row=0, column=2, pady=(4, 0))
        ctk.CTkLabel(self.metric_card, text="Saved Notes", font=ctk.CTkFont(size=10), text_color=t["sub"]).grid(row=1, column=2, pady=(0, 4))

        # 3. Main Scrollable HUD Content (Reminders, Profile, Memory Cards)
        self.brain_scroll = ctk.CTkScrollableFrame(self.right_pane, fg_color=t["card_inner"], corner_radius=8)
        self.brain_scroll.grid(row=2, column=0, sticky="nsew", padx=12, pady=0)
        self.brain_scroll.grid_columnconfigure(0, weight=1)

        # 4. Quick Action Shortcuts (Nexus Spatial Touchpoints)
        self.quick_actions_frame = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        self.quick_actions_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(6, 10))
        self.quick_actions_frame.grid_columnconfigure((0, 1, 2), weight=1)

        btn_brief = ctk.CTkButton(
            self.quick_actions_frame,
            text="☀️ Brief Me",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#006097",
            height=30,
            command=lambda: self.execute_shortcut("Jarvis brief me")
        )
        btn_brief.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        btn_weath = ctk.CTkButton(
            self.quick_actions_frame,
            text="🌦️ Weather",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#00838F",
            height=30,
            command=lambda: self.execute_shortcut("what is the weather in Dehradun")
        )
        btn_weath.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        btn_news = ctk.CTkButton(
            self.quick_actions_frame,
            text="📰 Live News",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#4527A0",
            height=30,
            command=lambda: self.execute_shortcut("tell me the latest headlines")
        )
        btn_news.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        btn_shot = ctk.CTkButton(
            self.quick_actions_frame,
            text="📸 Screenshot",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#004D40",
            height=30,
            command=lambda: self.execute_shortcut("take screenshot")
        )
        btn_shot.grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        btn_clip = ctk.CTkButton(
            self.quick_actions_frame,
            text="📋 Clipboard",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2E7D32",
            height=30,
            command=lambda: self.execute_shortcut("read my clipboard")
        )
        btn_clip.grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        btn_code = ctk.CTkButton(
            self.quick_actions_frame,
            text="💻 VS Code",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1565C0",
            height=30,
            command=lambda: self.execute_shortcut("open VS Code")
        )
        btn_code.grid(row=1, column=2, padx=2, pady=2, sticky="ew")

    # ==================== THEME & VISUAL MODE SWITCHING ====================
    def _on_theme_change(self, new_theme_name):
        if new_theme_name in SPATIAL_THEMES:
            self.current_theme_name = new_theme_name
            self.theme = SPATIAL_THEMES[new_theme_name]
            t = self.theme
            self.configure(fg_color=t["bg"])
            self.top_bar.configure(fg_color=t["card"])
            self.logo_lbl.configure(text_color=t["accent"])
            self.header_status.configure(text_color=t["accent"], fg_color=t["pill_bg"])
            self.left_pane.configure(fg_color=t["card"])
            self.right_pane.configure(fg_color=t["card"])
            self.canvas.configure(bg=t["canvas_bg"])
            self.transcript_box.configure(fg_color=t["card_inner"], text_color=t["text"])
            self.telemetry_card.configure(fg_color=t["card_inner"])
            self.metric_card.configure(fg_color=t["card_inner"])
            self.brain_scroll.configure(fg_color=t["card_inner"])
            self.banner_state.configure(text_color=t["accent"], fg_color=t["card_inner"])
            self.log_transcript("ENVIRONMENT", f"Shifted spatial realm to '{new_theme_name}'.", t["accent_alt"])
            audio_cues.play("confirm")

    def _toggle_visual_mode(self):
        if self.visual_mode == "SPHERE":
            self.visual_mode = "AVATAR"
            self.btn_mode_toggle.configure(text="🤖 Cyber Avatar")
            self.log_transcript("EMBODIMENT", "Digital Humanoid wireframe avatar online.", "#EA80FC")
        else:
            self.visual_mode = "SPHERE"
            self.btn_mode_toggle.configure(text="✨ 3D Orb")
            self.log_transcript("EMBODIMENT", "3D Hologram Particle Sphere online.", "#00FFCC")
        audio_cues.play("listen")

    # ==================== 3D HOLOGRAPHIC CORE ANIMATION (30 FPS) ====================
    def _animate_ai_core(self):
        self.animation_phase += 0.08
        self.canvas.delete("all")
        cx, cy = 140, 95
        state = self.assistant_state
        palette = self.theme["particles"]

        if state == "STOPPED":
            r = 34
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#12121E", outline="#37474F", width=2)
            self.canvas.create_text(cx, cy, text="STANDBY", font=("Segoe UI", 10, "bold"), fill="#546E7A")
            self.after(50, self._animate_ai_core)
            return

        if self.visual_mode == "AVATAR":
            # Futuristic Digital Humanoid Wireframe Face
            self._render_digital_avatar(cx, cy, state, palette)
        else:
            # 3D Rotating Holographic Particle Sphere
            self._render_3d_particle_sphere(cx, cy, state, palette)

        self.after(33, self._animate_ai_core)

    def _render_3d_particle_sphere(self, cx, cy, state, palette):
        phase = self.animation_phase
        if state == "IDLE":
            base_r = 52 + math.sin(phase * 1.5) * 3
            rot_speed = 0.5
        elif state == "LISTENING":
            base_r = 64 + math.sin(phase * 4.0) * 8
            rot_speed = 1.2
        elif state == "THINKING":
            base_r = 44 + math.sin(phase * 6.0) * 4
            rot_speed = 2.4
        elif state == "SPEAKING":
            base_r = 58 + math.sin(phase * 3.5) * 10
            rot_speed = 0.9

        yaw = phase * rot_speed
        pitch = phase * (rot_speed * 0.6)

        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)

        projected = []
        for i, (ox, oy, oz) in enumerate(_SPHERE_POINTS):
            # Y-axis rotation
            x1 = ox * cos_y - oz * sin_y
            y1 = oy
            z1 = ox * sin_y + oz * cos_y

            # X-axis rotation
            x2 = x1
            y2 = y1 * cos_p - z1 * sin_p
            z2 = y1 * sin_p + z1 * cos_p

            focal = 140
            scale = focal / (focal + z2 * base_r * 0.7)
            px = cx + x2 * base_r * scale
            py = cy + y2 * base_r * scale

            # Depth sorting score
            projected.append((z2, px, py, scale, i))

        # Render from back to front for depth
        projected.sort(key=lambda item: item[0])

        for z, px, py, scale, idx in projected:
            color = palette[idx % len(palette)]
            dot_r = max(1.2, (2.2 + z * 1.4) * scale)
            if z < -0.3:
                # Dim background particles
                self.canvas.create_oval(px-dot_r, py-dot_r, px+dot_r, py+dot_r, fill=color, outline="")
            else:
                # Bright foreground particles
                self.canvas.create_oval(px-dot_r, py-dot_r, px+dot_r, py+dot_r, fill=color, outline="")

        # Dynamic Equatorial Hologram Ring
        ring_r = base_r * 1.18
        self.canvas.create_oval(
            cx - ring_r, cy - ring_r * 0.32,
            cx + ring_r, cy + ring_r * 0.32,
            outline=palette[0], width=1
        )

    def _render_digital_avatar(self, cx, cy, state, palette):
        phase = self.animation_phase
        nod = math.sin(phase * 2) * 3 if state == "SPEAKING" else 0
        cy_nod = cy + nod

        # Hologram Wireframe Head Silhouette
        c_prim = palette[0]
        c_sec = palette[1]

        # Cranium and jaw polygons
        head_pts = [
            (cx - 38, cy_nod - 45), (cx + 38, cy_nod - 45),
            (cx + 46, cy_nod - 10), (cx + 30, cy_nod + 35),
            (cx, cy_nod + 52), (cx - 30, cy_nod + 35),
            (cx - 46, cy_nod - 10)
        ]
        self.canvas.create_polygon(head_pts, fill="", outline=c_prim, width=2)

        # Wireframe Brow & Cheekbones
        self.canvas.create_line(cx - 36, cy_nod - 10, cx + 36, cy_nod - 10, fill=c_sec, width=1)
        self.canvas.create_line(cx - 25, cy_nod + 15, cx + 25, cy_nod + 15, fill=c_sec, width=1)

        # Glowing Eyes with Blinking
        blink = math.sin(phase * 0.8) > 0.94
        eye_h = 1 if blink else 4
        self.canvas.create_oval(cx - 24, cy_nod - 12 - eye_h, cx - 12, cy_nod - 12 + eye_h, fill=c_prim, outline="")
        self.canvas.create_oval(cx + 12, cy_nod - 12 - eye_h, cx + 24, cy_nod - 12 + eye_h, fill=c_prim, outline="")

        # Audio-Reactive Mouth Line
        if state == "SPEAKING":
            mw = 10 + int(abs(math.sin(phase * 5.0) * 14))
            self.canvas.create_line(cx - mw, cy_nod + 28, cx + mw, cy_nod + 28, fill=c_prim, width=3)
        else:
            self.canvas.create_line(cx - 10, cy_nod + 28, cx + 10, cy_nod + 28, fill=c_sec, width=2)

    # ==================== STATE MANAGEMENT & GUIDANCE ====================
    def set_state(self, new_state: str, details: str = ""):
        self.assistant_state = new_state
        t = self.theme

        if new_state == "STOPPED":
            self.header_status.configure(text="⏸ MIC PAUSED", text_color="#FF9100", fg_color="#2D1A00")
            self.banner_state.configure(
                text="⏸ PAUSED — CLICK [MIC PAUSED] ABOVE TO RESUME LISTENING",
                text_color="#FFA726",
                fg_color=t["card_inner"]
            )

        elif new_state == "IDLE":
            music_player.unduck_audio()
            now_p = spotify_control.get_now_playing()
            if "Currently playing" in now_p:
                song_sub = now_p.replace("Currently playing ", "🎵 Spotify: ")
                banner_txt = f"{song_sub} — PRESS [Ctrl + Alt + J] TO COMMAND"
            else:
                banner_txt = "💤 DORMANT — PRESS [Ctrl + Alt + J] TO START"

            status_txt = "● READY (Ctrl+Alt+J)"
            self.header_status.configure(text=status_txt, text_color=t["accent"], fg_color=t["pill_bg"])
            self.banner_state.configure(
                text=banner_txt,
                text_color=t["accent"],
                fg_color=t["card_inner"]
            )

        elif new_state == "LISTENING":
            music_player.duck_audio()
            self.header_status.configure(text="🎙️ LISTENING TO YOU — SPEAK NOW", text_color="#00E5FF", fg_color="#002738")
            self.banner_state.configure(
                text="🎙️ LISTENING TO YOU — GO AHEAD, SPEAK FREELY!",
                text_color="#00E5FF",
                fg_color="#00384D"
            )

        elif new_state == "THINKING":
            self.header_status.configure(text="🧠 REASONING & EXECUTING...", text_color="#FFD54F", fg_color="#2E2000")
            msg = f"🧠 THINKING: {details}" if details else "🧠 REASONING, CALLING TOOLS & EXECUTING..."
            self.banner_state.configure(
                text=msg,
                text_color="#FFD54F",
                fg_color="#3E2E00"
            )

        elif new_state == "SPEAKING":
            music_player.duck_audio()
            self.header_status.configure(text="💬 JARVIS IS SPEAKING...", text_color="#B388FF", fg_color="#21103A")
            self.banner_state.configure(
                text="💬 JARVIS IS RESPONDING (Standing by next)...",
                text_color="#EA80FC",
                fg_color="#311B92"
            )

    def _interrupt_speech(self):
        voice.stop_speaking()
        audio_cues.play("stop")
        self.log_transcript("BARGE-IN", "Speech interrupted.", "#FF9100")
        self.set_state("LISTENING")

    # ==================== VOICE CHAT SESSION CONTROLS ====================
    def trigger_direct_listen(self):
        """Immediately wakes Jarvis up and listens for your command without requiring a wake word."""
        if self.assistant_busy:
            return
        self.is_session_active = True

        def _wake_and_prompt():
            audio_cues.play("listen")
            self.safe_after(0, lambda: self.set_state("SPEAKING"))
            greeting = "Yes, Nakul? I am listening."
            self.log_transcript("JARVIS", greeting, self.theme["accent_alt"])
            voice.speak(greeting)

            self.safe_after(0, lambda: self.set_state("LISTENING"))
            cmd = voice.listen_for_command(timeout=7, phrase_time_limit=10)
            if cmd:
                self._process_and_reply(cmd)
            else:
                self.safe_after(0, lambda: self.set_state("IDLE"))

        threading.Thread(target=_wake_and_prompt, daemon=True).start()

    def toggle_voice_session(self):
        if not self.is_assistant_running:
            self.is_assistant_running = True
            self.btn_talk_toggle.configure(text="🟢 MIC ACTIVE", fg_color="#004D40", hover_color="#00241B")
            audio_cues.play("confirm")
            self.set_state("IDLE")
            self.log_transcript("SYSTEM", "Microphone ready. Press [Ctrl + Alt + J] to speak.")
            
            if not self.voice_thread or not self.voice_thread.is_alive():
                self.voice_thread = threading.Thread(target=self._run_conversational_loop, daemon=True)
                self.voice_thread.start()
        else:
            self.is_assistant_running = False
            self.btn_talk_toggle.configure(text="⏸ MIC PAUSED", fg_color="#37474F", hover_color="#455A64")
            audio_cues.play("stop")
            music_player.stop()
            self.set_state("STOPPED")
            self.log_transcript("SYSTEM", "Microphone paused. Click 'MIC PAUSED' button above to resume.")

    def _register_global_hotkey(self):
        """Registers Ctrl+Alt+J global hotkey to start and close Jarvis."""
        def on_hotkey():
            now = time.time()
            if now - self._last_hotkey_time < 0.40:
                return
            self._last_hotkey_time = now
            print("[JarvisApp] Shortcut [Ctrl + Alt + J] triggered.")
            self._hotkey_event.set()

        try:
            import keyboard
            keyboard.add_hotkey("ctrl+alt+j", on_hotkey)
            print("[JarvisApp] Global Shortcut Active: Ctrl+Alt+J (keyboard hook)")
        except Exception:
            pass

        def win32_hotkey_worker():
            try:
                import ctypes
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                MOD_ALT = 0x0001
                MOD_CONTROL = 0x0002
                MOD_NOREPEAT = 0x4000
                HOTKEY_ID = 998
                VK_J = 0x4A

                if user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_J):
                    msg = wintypes.MSG()
                    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                        if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                            on_hotkey()
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageW(ctypes.byref(msg))
            except Exception:
                pass

        threading.Thread(target=win32_hotkey_worker, daemon=True).start()

    def _run_conversational_loop(self):
        """
        Shortcut-Driven Voice Loop:
        The microphone stays completely silent until the user presses [Ctrl + Alt + J].
        Pressing [Ctrl + Alt + J] starts listening directly (no wake word needed).
        Pressing [Ctrl + Alt + J] again closes Jarvis and stops listening/speaking.
        """
        try:
            voice.calibrate()
        except Exception as cal_err:
            print(f"[Jarvis Mic Calibration] {cal_err}")

        self.safe_after(0, lambda: self.set_state("IDLE"))

        while self.is_assistant_running:
            try:
                # Wait silently for [Ctrl + Alt + J]
                self._hotkey_event.wait()
                self._hotkey_event.clear()

                if not self.is_assistant_running:
                    break

                # If already active or speaking, stop/close!
                if self.assistant_busy:
                    voice.stop_speech()
                    audio_cues.play("stop")
                    self.assistant_busy = False
                    self.safe_after(0, lambda: self.set_state("IDLE"))
                    self.log_transcript("SYSTEM", "Stopped via [Ctrl + Alt + J].")
                    continue

                # START: Begin listening directly!
                audio_cues.play("wake")
                self.safe_after(0, lambda: self.set_state("LISTENING"))
                self.log_transcript("SYSTEM", "Activated via [Ctrl + Alt + J]. Listening...", self.theme["accent"])

                cmd = voice.listen_for_command(timeout=6.0, phrase_time_limit=12.0)

                # Check if hotkey was pressed to cancel while listening
                if self._hotkey_event.is_set():
                    self._hotkey_event.clear()
                    audio_cues.play("stop")
                    self.safe_after(0, lambda: self.set_state("IDLE"))
                    self.log_transcript("SYSTEM", "Closed via [Ctrl + Alt + J].")
                    continue

                if not cmd or not cmd.strip():
                    self.safe_after(0, lambda: self.set_state("IDLE"))
                    continue

                # Strip legacy wake words if spoken out of habit
                clean_cmd = cmd.strip()
                for prefix in ("hey jarvis", "hi jarvis", "jarvis", "हे जार्विस", "जार्विस", "hey jervis"):
                    if clean_cmd.lower().startswith(prefix):
                        clean_cmd = clean_cmd[len(prefix):].strip(",- ")
                if not clean_cmd:
                    clean_cmd = cmd.strip()

                if clean_cmd.lower() in ("goodbye", "bye", "sleep", "exit", "quit", "close"):
                    audio_cues.play("stop")
                    self.safe_after(0, lambda: self.set_state("IDLE"))
                    self.log_transcript("SYSTEM", "Closed via voice command.")
                    continue

                self._process_and_reply(clean_cmd)

            except Exception as loop_err:
                print(f"[Jarvis Voice Loop Error] {loop_err}")
                time.sleep(0.3)

    def _process_and_reply(self, user_text: str):
        self.assistant_busy = True
        self.log_transcript("YOU", user_text, self.theme["accent"])
        audio_cues.play("think")
        self.safe_after(0, lambda: self.set_state("THINKING", user_text[:32]))

        # Route to Gemini Agent with conversational memory or fast router
        reply, should_exit = commands.handle_command(user_text)
        self.log_transcript("JARVIS", reply, self.theme["accent_alt"])

        # Refresh memory and reminders cards
        self.safe_after(0, self.refresh_brain_view)
        self.safe_after(0, self.refresh_reminders_view)

        # Speak back with expressive voice
        self.safe_after(0, lambda: self.set_state("SPEAKING"))
        voice.speak(reply)

        if should_exit is True:
            self.log_transcript("SYSTEM", "Session ended.", "#FF1744")
            self.is_assistant_running = False
            self.safe_after(1000, self.destroy)
            return

        # If user explicitly told Jarvis to sleep/standby, return to cold sleep mode
        if should_exit == "sleep" and any(w in user_text.lower() for w in ("sleep", "standby", "goodbye", "bye", "stop listening")):
            self.is_session_active = False

        # Return directly to silent standby background mode!
        self.safe_after(0, lambda: self.set_state("IDLE"))
        self.assistant_busy = False

    def send_text_command(self):
        text = self.cmd_entry.get().strip()
        if not text:
            return
        self.cmd_entry.delete(0, "end")
        threading.Thread(target=lambda: self._process_and_reply(text), daemon=True).start()

    def execute_shortcut(self, cmd_text):
        threading.Thread(target=lambda: self._process_and_reply(cmd_text), daemon=True).start()

    # ==================== TRANSCRIPT & MEMORY LOGGING ====================
    def log_transcript(self, speaker: str, message: str, color: str = "#ECEFF1"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {speaker}: {message}\n\n"
        self.safe_after(0, lambda: self._insert_transcript(entry))

    def _insert_transcript(self, text: str):
        self.transcript_box.insert("end", text)
        self.transcript_box.see("end")

    def refresh_brain_view(self):
        data = memory_manager.load_memory()
        profile = data.get("user_profile", {})
        facts = data.get("facts", [])
        notes = data.get("notes", [])

        self.lbl_facts_num.configure(text=str(len(facts)))
        self.lbl_notes_num.configure(text=str(len(notes)))

        # Clear existing cards
        for child in self.brain_scroll.winfo_children():
            child.destroy()

        t = self.theme

        # 1. Profile Box
        p_frame = ctk.CTkFrame(self.brain_scroll, fg_color=t["card"], corner_radius=8)
        p_frame.pack(fill="x", padx=4, pady=3)
        ctk.CTkLabel(p_frame, text="👤 Nakul's Student Profile", font=ctk.CTkFont(size=12, weight="bold"), text_color=t["accent"]).pack(anchor="w", padx=10, pady=(6, 2))
        p_txt = f"{profile.get('education', 'B.Tech in Data Science')} | {profile.get('college', 'UPES')}\nGoal: {profile.get('career_goal', 'Data Scientist')}"
        ctk.CTkLabel(p_frame, text=p_txt, font=ctk.CTkFont(size=11), text_color="#90A4AE", justify="left").pack(anchor="w", padx=10, pady=(0, 6))

        # 2. Active Reminders List
        reminders = [r for r in reminder_scheduler.load_reminders() if not r.get("completed")]
        if reminders:
            ctk.CTkLabel(self.brain_scroll, text="⏰ Active Reminders & Schedules:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFD54F").pack(anchor="w", padx=6, pady=(8, 2))
            for r in reminders[:5]:
                rcard = ctk.CTkFrame(self.brain_scroll, fg_color=t["card"], corner_radius=6)
                rcard.pack(fill="x", padx=4, pady=2)
                ctk.CTkLabel(rcard, text=f"• {r.get('text', '')}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ECEFF1", justify="left").pack(anchor="w", padx=8, pady=(4, 1))
                ctk.CTkLabel(rcard, text=f"Due: {r.get('target_time', '')}", font=ctk.CTkFont(size=9), text_color="#FFA726").pack(anchor="w", padx=8, pady=(0, 4))

        # 3. Learned Facts
        if facts:
            ctk.CTkLabel(self.brain_scroll, text="🧠 Memory Points Learned:", font=ctk.CTkFont(size=12, weight="bold"), text_color=t["accent_alt"]).pack(anchor="w", padx=6, pady=(8, 2))
            for f in reversed(facts[-6:]):
                card = ctk.CTkFrame(self.brain_scroll, fg_color=t["card"], corner_radius=6)
                card.pack(fill="x", padx=4, pady=2)
                ctk.CTkLabel(card, text=f"• {f.get('fact', '')}", font=ctk.CTkFont(size=11), text_color="#ECEFF1", wraplength=310, justify="left").pack(anchor="w", padx=8, pady=(4, 1))
                ctk.CTkLabel(card, text=f"{f.get('timestamp', '')}", font=ctk.CTkFont(size=9), text_color="#546E7A").pack(anchor="w", padx=8, pady=(0, 4))

        # 4. Notes
        if notes:
            ctk.CTkLabel(self.brain_scroll, text="📝 Stored Notepad Entries:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#B388FF").pack(anchor="w", padx=6, pady=(8, 2))
            for n in reversed(notes[-3:]):
                n_card = ctk.CTkFrame(self.brain_scroll, fg_color=t["card"], corner_radius=6)
                n_card.pack(fill="x", padx=4, pady=2)
                ctk.CTkLabel(n_card, text=f"[{n.get('title')}]: {n.get('content')}", font=ctk.CTkFont(size=11), text_color="#ECEFF1", wraplength=310, justify="left").pack(anchor="w", padx=8, pady=(4, 1))

    def refresh_reminders_view(self):
        active = [r for r in reminder_scheduler.load_reminders() if not r.get("completed")]
        self.lbl_reminders_num.configure(text=str(len(active)))
        self.refresh_brain_view()

    # ==================== PERIODIC TELEMETRY LOOP ====================
    def _periodic_telemetry_loop(self):
        def _fetch():
            try:
                cpu = psutil.cpu_percent(interval=0.1)
                ram = psutil.virtual_memory().percent
                bat = psutil.sensors_battery()
                bat_str = f"BAT: {bat.percent}%" if bat else "PWR: AC"
                
                # Fetch weather once in background
                weather_str = "🌦️ Dehradun"
                try:
                    w = live_knowledge.get_live_weather("Dehradun")
                    if "currently" in w:
                        temp = w.split("currently ")[1].split("°C")[0]
                        weather_str = f"🌦️ Dehradun: {temp}°C"
                except Exception:
                    pass

                self.safe_after(0, lambda: self._apply_telemetry(cpu, ram, bat_str, weather_str))
            except Exception:
                pass

        threading.Thread(target=_fetch, daemon=True).start()
        self.after(5000, self._periodic_telemetry_loop)

    def _apply_telemetry(self, cpu, ram, bat_str, weather_str):
        self.lbl_cpu.configure(text=f"CPU: {cpu:.0f}%")
        self.lbl_ram.configure(text=f"RAM: {ram:.0f}%")
        self.lbl_bat.configure(text=bat_str)
        self.lbl_weather.configure(text=weather_str)


def main():
    app = JarvisApp()
    app.mainloop()

if __name__ == "__main__":
    main()

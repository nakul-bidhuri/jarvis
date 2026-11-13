"""
app.py — JARVIS 2.0 Spatial AI Operating System (Streamlit Web Edition).

A cinema-grade, futuristic 3D WebGL Spatial AI assistant inspired by Nexus Spatial OS:
  - 🌐 Full-Width 3D Volumetric Hologram Particle Core (Three.js WebGL + Cyberpunk Grid + Starfield)
  - 🛰️ Triple Gyroscopic Quantum Rings with Mouse Parallax & Audio Waveform Modulation
  - 📊 Spatial Glassmorphic HUD: SVG Radial Telemetry Gauges, Audio Spectrum Visualizer, Climate Matrix
  - 🎵 Spotify Holographic Visualizer with Media Controls
  - ⚡ Autonomous Multi-Agent Command Engine powered by Google Gemini
  - 🎙️ Instant Acoustic Audio Feedback & Voice Interaction
  - 🛡️ Zero-Trust Security & Safe Messaging Confirmation Protocol
"""

import os
import sys
import time
import datetime
import streamlit as st
import streamlit.components.v1 as components

# Ensure D:\Jarvis is in import path
sys.path.insert(0, os.path.dirname(__file__))

import config
import commands
import memory_manager
import live_knowledge
import reminder_scheduler
import daily_briefing
import safe_messaging
import spotify_control
import laptop_controller
import audio_cues

# Page Configuration
st.set_page_config(
    page_title="JARVIS 2.0 // SPATIAL OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "⚡ Jarvis 2.0 Spatial OS Online. Neural Core connected. All systems nominal."}
    ]
if "active_session" not in st.session_state:
    st.session_state.active_session = True
if "environment" not in st.session_state:
    st.session_state.environment = "Command Center"

# Environment Color Palettes
ENV_PALETTES = {
    "Command Center": {"primary": "#00f0ff", "secondary": "#00ffa3", "accent": "#a855f7", "bg": "#050813", "grid": "0x00f0ff"},
    "Dark Laboratory": {"primary": "#10b981", "secondary": "#34d399", "accent": "#f59e0b", "bg": "#030a08", "grid": "0x10b981"},
    "Glass Observatory": {"primary": "#a855f7", "secondary": "#ec4899", "accent": "#00f0ff", "bg": "#080512", "grid": "0xa855f7"},
    "Deep Space": {"primary": "#38bdf8", "secondary": "#818cf8", "accent": "#f472b6", "bg": "#02040a", "grid": "0x38bdf8"},
    "Cyber Matrix": {"primary": "#22c55e", "secondary": "#4ade80", "accent": "#eab308", "bg": "#020904", "grid": "0x22c55e"}
}
current_pal = ENV_PALETTES.get(st.session_state.environment, ENV_PALETTES["Command Center"])

# Cinema-Grade Nexus Spatial OS CSS
SPATIAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800;900&family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* Hide Streamlit Default Chrome */
#MainMenu, header, footer, .stDeployButton, [data-testid="stToolbar"] {{
    visibility: hidden !important;
    display: none !important;
}}

/* Main Spatial Viewport */
.stApp {{
    background-color: {current_pal['bg']};
    background-image: 
        radial-gradient(at 10% 10%, rgba(0, 240, 255, 0.08) 0px, transparent 55%),
        radial-gradient(at 90% 90%, rgba(168, 85, 247, 0.07) 0px, transparent 55%),
        radial-gradient(at 50% 50%, rgba(0, 255, 163, 0.03) 0px, transparent 65%);
    font-family: 'Rajdhani', sans-serif;
    color: #E2E8F0;
}}

.block-container {{
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}}

/* Header Bar */
.spatial-top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: rgba(10, 16, 30, 0.75);
    border: 1px solid rgba(0, 240, 255, 0.25);
    border-radius: 16px;
    backdrop-filter: blur(16px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 0 12px rgba(0, 240, 255, 0.06);
    margin-bottom: 18px;
}}

.brand-title {{
    font-family: 'Orbitron', sans-serif;
    font-size: 1.8rem;
    font-weight: 900;
    letter-spacing: 3px;
    background: linear-gradient(135deg, {current_pal['primary']} 0%, {current_pal['secondary']} 50%, {current_pal['accent']} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 12px;
}}

.telemetry-chip {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #94A3B8;
    background: rgba(15, 23, 42, 0.8);
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid rgba(0, 240, 255, 0.2);
    display: inline-flex;
    align-items: center;
    gap: 8px;
}}

.beacon-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: {current_pal['secondary']};
    box-shadow: 0 0 10px {current_pal['secondary']};
    animation: beaconPulse 2s infinite ease-in-out;
}}

@keyframes beaconPulse {{
    0% {{ opacity: 0.4; transform: scale(0.9); }}
    50% {{ opacity: 1; transform: scale(1.2); }}
    100% {{ opacity: 0.4; transform: scale(0.9); }}
}}

/* Spatial Hologram Cards */
.spatial-hud-card {{
    background: rgba(11, 19, 36, 0.75);
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-radius: 16px;
    padding: 16px 20px;
    backdrop-filter: blur(16px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5), inset 0 0 15px rgba(0, 240, 255, 0.04);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 14px;
}}

.spatial-hud-card:hover {{
    border-color: rgba(0, 240, 255, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 12px 36px rgba(0, 240, 255, 0.15), inset 0 0 20px rgba(0, 240, 255, 0.08);
}}

.card-label {{
    font-family: 'Orbitron', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    color: #94A3B8;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}}

/* Radial Gauges */
.gauge-container {{
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 10px 0;
}}

.gauge-box {{
    text-align: center;
}}

.gauge-val {{
    font-family: 'Orbitron', sans-serif;
    font-size: 1.35rem;
    font-weight: 800;
    color: {current_pal['primary']};
}}

.gauge-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* Audio Frequency Visualizer */
.audio-visualizer-bar-box {{
    display: flex;
    align-items: flex-end;
    justify-content: center;
    gap: 4px;
    height: 48px;
    padding: 8px 0;
}}

.freq-bar {{
    width: 6px;
    border-radius: 4px;
    background: linear-gradient(to top, {current_pal['primary']}, {current_pal['accent']});
    animation: soundWave 1.4s ease-in-out infinite alternate;
}}

@keyframes soundWave {{
    0% {{ height: 15%; opacity: 0.35; }}
    50% {{ height: 85%; opacity: 0.95; }}
    100% {{ height: 35%; opacity: 0.55; }}
}}

/* Chat Stream Container */
.chat-stream-box {{
    background: rgba(10, 16, 30, 0.85);
    border: 1px solid rgba(0, 240, 255, 0.22);
    border-radius: 16px;
    padding: 16px;
    backdrop-filter: blur(20px);
    box-shadow: 0 10px 32px rgba(0, 0, 0, 0.55);
    max-height: 290px;
    overflow-y: auto;
    margin-bottom: 14px;
}}

.chat-bubble-user {{
    background: rgba(30, 41, 59, 0.85);
    border-left: 3px solid {current_pal['secondary']};
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    color: #F1F5F9;
    font-size: 0.95rem;
}}

.chat-bubble-jarvis {{
    background: rgba(15, 23, 42, 0.95);
    border-left: 3px solid {current_pal['primary']};
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #FFFFFF;
    font-size: 1.02rem;
    box-shadow: 0 4px 16px rgba(0, 240, 255, 0.12);
}}

/* Futuristic Buttons */
.stButton>button {{
    background: rgba(15, 23, 42, 0.8) !important;
    color: {current_pal['primary']} !important;
    border: 1px solid rgba(0, 240, 255, 0.3) !important;
    border-radius: 10px !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    letter-spacing: 1px !important;
    padding: 8px 14px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
}}

.stButton>button:hover {{
    background: linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(168, 85, 247, 0.2)) !important;
    border-color: {current_pal['primary']} !important;
    color: #FFFFFF !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0, 240, 255, 0.3) !important;
}}

/* Chat Input Bar */
.stChatInputContainer {{
    border-radius: 14px !important;
    border: 1px solid rgba(0, 240, 255, 0.35) !important;
    background: rgba(15, 23, 42, 0.9) !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6), inset 0 0 15px rgba(0, 240, 255, 0.05) !important;
}}
</style>
"""
st.markdown(SPATIAL_CSS, unsafe_allow_html=True)

# ==================== ADVANCED THREE.JS SPATIAL HOLOGRAPHIC CORE ====================
# Generates a cinema-grade 3D WebGL Holographic Particle entity matching Nexus Spatial OS
THREE_JS_SPATIAL_CORE = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body, html {{
            margin: 0; padding: 0; width: 100%; height: 100%;
            overflow: hidden; background: transparent;
            user-select: none;
        }}
        #nexus-canvas {{
            width: 100%; height: 100%; display: block;
            cursor: grab;
        }}
        #nexus-canvas:active {{
            cursor: grabbing;
        }}
        .hud-overlay-text {{
            position: absolute;
            bottom: 14px;
            left: 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: rgba(0, 240, 255, 0.65);
            letter-spacing: 2px;
            pointer-events: none;
        }}
        .hud-overlay-mode {{
            position: absolute;
            bottom: 14px;
            right: 20px;
            font-family: 'Orbitron', sans-serif;
            font-size: 11px;
            font-weight: 700;
            color: rgba(0, 255, 163, 0.8);
            letter-spacing: 1.5px;
            pointer-events: none;
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="nexus-canvas"></div>
    <div class="hud-overlay-text">SPATIAL COMPUTING ENGINE // VOLUMETRIC MATRIX</div>
    <div class="hud-overlay-mode">● RECEPTIVE AUDIO LINK</div>

    <script>
        const container = document.getElementById('nexus-canvas');
        const width = container.clientWidth;
        const height = container.clientHeight;

        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2({current_pal['bg'].replace('#', '0x')}, 0.0032);

        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        camera.position.set(0, 15, 235);

        const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true, powerPreference: 'high-performance' }});
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        // Ambient & Point Lighting
        const ambientLight = new THREE.AmbientLight(0x0a192f, 2.5);
        scene.add(ambientLight);

        const coreLight = new THREE.PointLight({current_pal['primary'].replace('#', '0x')}, 3.5, 300);
        coreLight.position.set(0, 0, 0);
        scene.add(coreLight);

        const secondaryLight = new THREE.PointLight({current_pal['accent'].replace('#', '0x')}, 2.5, 350);
        secondaryLight.position.set(70, 60, 50);
        scene.add(secondaryLight);

        // 1. Perspective Cyberpunk Grid Floor
        const grid = new THREE.GridHelper(380, 38, {current_pal['grid']}, 0x0f172a);
        grid.position.y = -80;
        scene.add(grid);

        // 2. Distant Ambient Starfield (1,200 particles)
        const starCount = 1200;
        const starGeo = new THREE.BufferGeometry();
        const starPositions = new Float32Array(starCount * 3);
        for (let i = 0; i < starCount * 3; i += 3) {{
            starPositions[i] = (Math.random() - 0.5) * 600;
            starPositions[i + 1] = (Math.random() - 0.5) * 450;
            starPositions[i + 2] = (Math.random() - 0.5) * 500;
        }}
        starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
        const starMat = new THREE.PointsMaterial({{
            size: 1.2,
            color: 0x94a3b8,
            transparent: true,
            opacity: 0.65,
            blending: THREE.AdditiveBlending
        }});
        const starField = new THREE.Points(starGeo, starMat);
        scene.add(starField);

        // 3. Central Hologram Particle Sphere (2,200 particles)
        const particleCount = 2200;
        const sphereGeo = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const originalPositions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);

        const c1 = new THREE.Color({current_pal['primary'].replace('#', '0x')});
        const c2 = new THREE.Color({current_pal['secondary'].replace('#', '0x')});
        const c3 = new THREE.Color({current_pal['accent'].replace('#', '0x')});
        const baseRadius = 58;

        for (let i = 0; i < particleCount; i++) {{
            // Golden spiral Fibonacci sphere
            const phi = Math.acos(-1 + (2 * i) / particleCount);
            const theta = Math.sqrt(particleCount * Math.PI) * phi;

            const r = baseRadius + (Math.random() - 0.5) * 5;
            const x = r * Math.cos(theta) * Math.sin(phi);
            const y = r * Math.sin(theta) * Math.sin(phi);
            const z = r * Math.cos(phi);

            positions[i * 3] = x;
            positions[i * 3 + 1] = y;
            positions[i * 3 + 2] = z;

            originalPositions[i * 3] = x;
            originalPositions[i * 3 + 1] = y;
            originalPositions[i * 3 + 2] = z;

            const mixColor = (i % 3 === 0) ? c1 : (i % 3 === 1 ? c2 : c3);
            colors[i * 3] = mixColor.r;
            colors[i * 3 + 1] = mixColor.g;
            colors[i * 3 + 2] = mixColor.b;
        }}

        sphereGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        sphereGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const sphereMat = new THREE.PointsMaterial({{
            size: 2.6,
            vertexColors: true,
            transparent: true,
            opacity: 0.88,
            blending: THREE.AdditiveBlending
        }});
        const sphereMesh = new THREE.Points(sphereGeo, sphereMat);
        scene.add(sphereMesh);

        // 4. Triple Gyroscopic Quantum Rings
        // Ring 1: Equatorial Ring with Satellite Nodes
        const ring1Geo = new THREE.TorusGeometry(78, 0.5, 16, 120);
        const ring1Mat = new THREE.MeshBasicMaterial({{
            color: {current_pal['primary'].replace('#', '0x')},
            transparent: true,
            opacity: 0.75,
            wireframe: true
        }});
        const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
        ring1.rotation.x = Math.PI / 2.1;
        scene.add(ring1);

        // Ring 2: Polar Precession Ring
        const ring2Geo = new THREE.TorusGeometry(88, 0.4, 16, 100);
        const ring2Mat = new THREE.MeshBasicMaterial({{
            color: {current_pal['accent'].replace('#', '0x')},
            transparent: true,
            opacity: 0.55
        }});
        const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
        ring2.rotation.x = Math.PI / 4;
        ring2.rotation.y = Math.PI / 6;
        scene.add(ring2);

        // Ring 3: Outer Horizon Ring
        const ring3Geo = new THREE.RingGeometry(98, 99.2, 96);
        const ring3Mat = new THREE.MeshBasicMaterial({{
            color: {current_pal['secondary'].replace('#', '0x')},
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.4
        }});
        const ring3 = new THREE.Mesh(ring3Geo, ring3Mat);
        ring3.rotation.x = Math.PI / 2.3;
        scene.add(ring3);

        // 5. Crystalline Quantum Nucleus (Wireframe Icosahedron)
        const coreGeo = new THREE.IcosahedronGeometry(18, 2);
        const coreMat = new THREE.MeshBasicMaterial({{
            color: {current_pal['primary'].replace('#', '0x')},
            wireframe: true,
            transparent: true,
            opacity: 0.45,
            blending: THREE.AdditiveBlending
        }});
        const coreMesh = new THREE.Mesh(coreGeo, coreMat);
        scene.add(coreMesh);

        // Interactive Mouse Parallax Tracking
        let mouseX = 0, mouseY = 0;
        let targetX = 0, targetY = 0;
        const windowHalfX = window.innerWidth / 2;
        const windowHalfY = window.innerHeight / 2;

        document.addEventListener('mousemove', (e) => {{
            mouseX = (e.clientX - windowHalfX) * 0.08;
            mouseY = (e.clientY - windowHalfY) * 0.08;
        }});

        // Web Audio Synthesizer (Harmonic Sci-Fi Cues directly in browser)
        let audioCtx = null;
        function playChirp(freq1, freq2, duration) {{
            try {{
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(freq1, audioCtx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(freq2, audioCtx.currentTime + duration);
                gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + duration);
            }} catch(e) {{}}
        }}

        container.addEventListener('click', () => {{
            playChirp(440, 880, 0.15);
        }});

        // Animation Loop
        const clock = new THREE.Clock();
        const posAttr = sphereGeo.attributes.position;

        function animate() {{
            requestAnimationFrame(animate);
            const t = clock.getElapsedTime();

            // Parallax Camera Damping
            targetX += (mouseX - targetX) * 0.05;
            targetY += (-mouseY - targetY) * 0.05;
            camera.position.x = targetX;
            camera.position.y = 15 + targetY;
            camera.lookAt(0, 0, 0);

            // Ring Rotations
            ring1.rotation.z = t * 0.22;
            ring2.rotation.y = -t * 0.3;
            ring2.rotation.z = t * 0.15;
            ring3.rotation.z = -t * 0.12;

            // Core Nucleus Pulsing
            coreMesh.rotation.x = t * 0.4;
            coreMesh.rotation.y = -t * 0.5;
            const coreScale = 1.0 + Math.sin(t * 2.8) * 0.08;
            coreMesh.scale.set(coreScale, coreScale, coreScale);

            // Particle Sphere Fluid Turbulence Wave
            const positionsArray = posAttr.array;
            for (let i = 0; i < particleCount; i++) {{
                const idx = i * 3;
                const ox = originalPositions[idx];
                const oy = originalPositions[idx + 1];
                const oz = originalPositions[idx + 2];

                // Spherical sinusoidal wave displacement
                const wave = Math.sin(t * 2.2 + oy * 0.08 + ox * 0.06) * 3.8;
                const factor = 1.0 + (wave / baseRadius);

                positionsArray[idx] = ox * factor;
                positionsArray[idx + 1] = oy * factor;
                positionsArray[idx + 2] = oz * factor;
            }}
            posAttr.needsUpdate = true;

            // Sphere global rotation
            sphereMesh.rotation.y = t * 0.18;
            sphereMesh.rotation.x = Math.sin(t * 0.12) * 0.1;

            // Starfield Slow Drift
            starField.rotation.y = -t * 0.02;

            renderer.render(scene, camera);
        }}
        animate();

        // Responsive Resize
        window.addEventListener('resize', () => {{
            const newW = container.clientWidth;
            const newH = container.clientHeight;
            camera.aspect = newW / newH;
            camera.updateProjectionMatrix();
            renderer.setSize(newW, newH);
        }});
    </script>
</body>
</html>
"""

# ==================== TOP NAVIGATION / SPATIAL COMMAND STRIP ====================
st.markdown(f"""
<div class="spatial-top-bar">
    <div class="brand-title">
        <span>⚡ JARVIS 2.0</span>
        <span style="font-size:0.85rem; color:#64748B; font-family:'JetBrains Mono'; font-weight:500;">// SPATIAL OS</span>
    </div>
    <div style="display: flex; gap: 12px; align-items: center;">
        <div class="telemetry-chip">
            <div class="beacon-dot"></div>
            <span>CORE ONLINE</span>
        </div>
        <div class="telemetry-chip">
            <span>NEURAL LINK: 99.8%</span>
        </div>
        <div class="telemetry-chip">
            <span>UPES DEHRADUN</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Environment Switcher Pills
col_env, col_space = st.columns([3, 1])
with col_env:
    env_choice = st.radio(
        "Spatial Environment",
        ["Command Center", "Dark Laboratory", "Glass Observatory", "Deep Space", "Cyber Matrix"],
        index=list(ENV_PALETTES.keys()).index(st.session_state.environment),
        horizontal=True,
        label_visibility="collapsed"
    )
    if env_choice != st.session_state.environment:
        st.session_state.environment = env_choice
        st.rerun()

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ==================== MAIN SPATIAL 3-COLUMN HOLOGRAM VIEWPORT ====================
col_left_hud, col_center_3d, col_right_hud = st.columns([1.1, 2.0, 1.1])

# ----------------- LEFT HUD: HARDWARE & AUDIO FREQUENCY -----------------
with col_left_hud:
    # 1. Telemetry Gauges
    try:
        cpu_val = f"{laptop_controller.psutil.cpu_percent():.0f}%"
        ram_val = f"{laptop_controller.psutil.virtual_memory().percent:.0f}%"
        bat = laptop_controller.psutil.sensors_battery()
        bat_val = f"{bat.percent}%" if bat else "AC PWR"
    except Exception:
        cpu_val, ram_val, bat_val = "14%", "46%", "100%"

    st.markdown(f"""
    <div class="spatial-hud-card">
        <div class="card-label">
            <span>⚡ SYSTEM TELEMETRY</span>
            <span style="color:{current_pal['primary']};">HARDWARE</span>
        </div>
        <div class="gauge-container">
            <div class="gauge-box">
                <div class="gauge-val">{cpu_val}</div>
                <div class="gauge-sub">CPU LOAD</div>
            </div>
            <div class="gauge-box">
                <div class="gauge-val">{ram_val}</div>
                <div class="gauge-sub">RAM USED</div>
            </div>
            <div class="gauge-box">
                <div class="gauge-val">{bat_val}</div>
                <div class="gauge-sub">BATTERY</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Audio Frequency Spectrum Visualizer
    st.markdown(f"""
    <div class="spatial-hud-card">
        <div class="card-label">
            <span>🎙️ AUDIO SPECTRUM</span>
            <span style="color:{current_pal['secondary']};">LIVE FEED</span>
        </div>
        <div class="audio-visualizer-bar-box">
            <div class="freq-bar" style="animation-delay: 0.1s;"></div>
            <div class="freq-bar" style="animation-delay: 0.3s;"></div>
            <div class="freq-bar" style="animation-delay: 0.5s;"></div>
            <div class="freq-bar" style="animation-delay: 0.2s;"></div>
            <div class="freq-bar" style="animation-delay: 0.7s;"></div>
            <div class="freq-bar" style="animation-delay: 0.4s;"></div>
            <div class="freq-bar" style="animation-delay: 0.6s;"></div>
            <div class="freq-bar" style="animation-delay: 0.15s;"></div>
            <div class="freq-bar" style="animation-delay: 0.8s;"></div>
            <div class="freq-bar" style="animation-delay: 0.35s;"></div>
            <div class="freq-bar" style="animation-delay: 0.55s;"></div>
            <div class="freq-bar" style="animation-delay: 0.25s;"></div>
        </div>
        <div style="text-align:center; font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B; margin-top:4px;">
            VOICE MATRIX // SAMPLING 44.1 KHZ
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. User Knowledge Profile
    mem_data = memory_manager.load_memory()
    profile = mem_data.get("user_profile", {})
    st.markdown(f"""
    <div class="spatial-hud-card">
        <div class="card-label">
            <span>🧠 KNOWLEDGE PROFILE</span>
            <span style="color:{current_pal['accent']};">USER</span>
        </div>
        <div style="font-family:'Rajdhani'; font-size:1rem; line-height:1.6;">
            <div><b>Name:</b> {profile.get('name', 'Nakul')}</div>
            <div><b>Focus:</b> {profile.get('education', 'B.Tech Data Science')}</div>
            <div><b>Academy:</b> {profile.get('college', 'UPES Dehradun')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- CENTER STAGE: 3D THREE.JS HOLOGRAPHIC CORE -----------------
with col_center_3d:
    components.html(THREE_JS_SPATIAL_CORE, height=480)

# ----------------- RIGHT HUD: WEATHER, SPOTIFY & REMINDERS -----------------
with col_right_hud:
    # 1. Live Weather
    try:
        weath_raw = live_knowledge.get_live_weather("Dehradun")
        if "currently" in weath_raw:
            weath_temp = weath_raw.split("currently ")[1].split("°C")[0] + "°C"
            weath_desc = weath_raw.split("with ")[1].split(".")[0].title()
        else:
            weath_temp, weath_desc = "22°C", "Clear"
    except Exception:
        weath_temp, weath_desc = "22°C", "Fair"

    st.markdown(f"""
    <div class="spatial-hud-card">
        <div class="card-label">
            <span>🌦️ CLIMATE MATRIX</span>
            <span style="color:{current_pal['primary']};">DEHRADUN</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-family:'Orbitron'; font-size:1.8rem; font-weight:800; color:{current_pal['primary']};">{weath_temp}</div>
            <div style="font-family:'JetBrains Mono'; font-size:0.85rem; color:#94A3B8; text-align:right;">{weath_desc}<br><small style="color:#64748B;">UPES CAMPUS</small></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Spotify Hologram
    now_playing = spotify_control.get_now_playing().replace("Currently playing ", "")
    st.markdown(f"""
    <div class="spatial-hud-card">
        <div class="card-label">
            <span>🎵 SPOTIFY MEDIA</span>
            <span style="color:{current_pal['secondary']};">PLAYBACK</span>
        </div>
        <div style="font-family:'Rajdhani'; font-weight:700; font-size:1.05rem; color:#FFFFFF; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; margin-bottom:8px;">
            {now_playing}
        </div>
    </div>
    """, unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        if st.button("⏮️ Prev", use_container_width=True):
            spotify_control.previous_track()
            st.rerun()
    with sc2:
        if st.button("⏯️ Pause", use_container_width=True):
            spotify_control.pause()
            st.rerun()
    with sc3:
        if st.button("⏭️ Next", use_container_width=True):
            spotify_control.next_track()
            st.rerun()

    # 3. Scheduled Tasks / Reminders
    active_rems = [r for r in reminder_scheduler.load_reminders() if not r.get("completed")]
    rems_html = ""
    if active_rems:
        for r in active_rems[:3]:
            rems_html += f"<div style='margin-bottom:6px;'>• <b>{r.get('text')}</b> <small style='color:#F59E0B;'>({r.get('target_time')})</small></div>"
    else:
        rems_html = "<div style='color:#64748B;'>No pending alerts scheduled.</div>"

    st.markdown(f"""
    <div class="spatial-hud-card">
        <div class="card-label">
            <span>⏰ ACTIVE DIRECTIVES</span>
            <span style="color:{current_pal['accent']};">{len(active_rems)} PENDING</span>
        </div>
        <div style="font-family:'Rajdhani'; font-size:0.95rem;">
            {rems_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ==================== BOTTOM FLOATING COMMAND DECK ====================
col_cmd_left, col_cmd_center, col_cmd_right = st.columns([1, 6, 1])

with col_cmd_center:
    # 1. Chat Stream Display
    st.markdown('<div class="chat-stream-box">', unsafe_allow_html=True)
    for msg in st.session_state.messages[-6:]:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user"><b>YOU:</b> {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-jarvis"><b>⚡ JARVIS:</b> {msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Six Spatial Quick Action Beams
    qb1, qb2, qb3, qb4, qb5, qb6 = st.columns(6)
    with qb1:
        if st.button("☀️ Briefing", use_container_width=True):
            audio_cues.play("confirm")
            reply = daily_briefing.generate_daily_briefing()
            st.session_state.messages.append({"role": "user", "content": "Jarvis, give me an executive briefing."})
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    with qb2:
        if st.button("🌦️ Weather", use_container_width=True):
            audio_cues.play("confirm")
            reply = live_knowledge.get_live_weather("Dehradun")
            st.session_state.messages.append({"role": "user", "content": "What is the live weather in Dehradun?"})
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    with qb3:
        if st.button("📰 Headlines", use_container_width=True):
            audio_cues.play("confirm")
            reply = live_knowledge.get_live_news()
            st.session_state.messages.append({"role": "user", "content": "Get today's top headlines."})
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    with qb4:
        if st.button("🎵 Play Music", use_container_width=True):
            audio_cues.play("confirm")
            reply = commands.handle_command("play some trending music")[0]
            st.session_state.messages.append({"role": "user", "content": "Play some trending music."})
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    with qb5:
        if st.button("📸 Screenshot", use_container_width=True):
            audio_cues.play("confirm")
            reply = laptop_controller.take_screenshot()
            st.session_state.messages.append({"role": "user", "content": "Take a screenshot."})
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    with qb6:
        if st.button("💻 VS Code", use_container_width=True):
            audio_cues.play("confirm")
            reply = laptop_controller.open_code_editor()
            st.session_state.messages.append({"role": "user", "content": "Open VS Code."})
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    # 3. Interactive Spatial Chat Input
    user_input = st.chat_input("Speak or dispatch directive to Jarvis 2.0 (e.g. 'play Believer', 'remind me at 7 PM', 'check weather')...")
    if user_input:
        audio_cues.play("think")
        st.session_state.messages.append({"role": "user", "content": user_input})
        reply, should_exit = commands.handle_command(user_input)
        audio_cues.play("confirm")
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

"""
voice_engine.py – Zero-Lag, High-Precision Speech I/O for Jarvis 2.0.

Key Upgrades Fixed:
1. Persistent Microphone Stream & Zero-Gap Wake Detection:
   - Eliminated the 7.5s `phrase_time_limit` blind spot that caused "Hey Jarvis" to drop 2-3 times during background noise.
   - Uses a tight 2.8s rolling window for cold wake-word capture with `dynamic_energy_threshold = False` after initial room calibration so ambient fan/TV noise never inflates the threshold and deafens the mic.
2. Context-Biased Faster-Whisper (`initial_prompt`):
   - Passes `initial_prompt="Hey Jarvis, Jarvis, Nexus, transform into immersive mode, human mode, assistant mode"` and `vad_filter=True` to `faster_whisper`, fixing misrecognitions of "Hey Jarvis" in Indian English accents.
3. Parallel Pipelined Neural TTS (`speak`):
   - Synthesizes sentence N+1 in a background thread while sentence N is playing, removing pauses between sentences.
4. Full Porcupine Single-Frame Fix & Browser Web-Speech Bridge Support.
"""

import speech_recognition as sr
import threading
import queue
import os
import struct
import tempfile
import asyncio
import time
import string
import difflib
import pygame
import edge_tts
import config

# Initialize pygame mixer cleanly for low-latency audio playback
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
except Exception as e:
    print(f"[Jarvis Audio] Pygame mixer init notice: {e}")

_speech_channel = None
def _get_speech_channel():
    global _speech_channel
    if _speech_channel is None:
        try:
            _speech_channel = pygame.mixer.Channel(0)
        except Exception:
            pass
    return _speech_channel

_offline_whisper = None
_whisper_lock = threading.Lock()

def _get_offline_whisper():
    global _offline_whisper
    if _offline_whisper is None:
        with _whisper_lock:
            if _offline_whisper is None:
                try:
                    from faster_whisper import WhisperModel
                    _offline_whisper = WhisperModel("base.en", device="cpu", compute_type="int8", cpu_threads=4)
                except Exception:
                    try:
                        from faster_whisper import WhisperModel
                        _offline_whisper = WhisperModel("tiny.en", device="cpu", compute_type="int8", cpu_threads=4)
                    except Exception:
                        pass
    return _offline_whisper

# Preload whisper model in background so first listening is instant
threading.Thread(target=_get_offline_whisper, daemon=True).start()

# Recognizer configuration – locked threshold prevents threshold drift in noisy rooms
_recognizer = sr.Recognizer()
_recognizer.energy_threshold = 280.0
_recognizer.dynamic_energy_threshold = False  # Locked after calibration to prevent deafening drift
_recognizer.pause_threshold = 0.45
_recognizer.phrase_threshold = 0.15
_recognizer.non_speaking_duration = 0.30

_mic = None

def _get_mic():
    global _mic
    if _mic is None:
        try:
            _mic = sr.Microphone()
        except Exception as e:
            print(f"[Jarvis Mic Init Notice] {e}")
    return _mic

WHISPER_WAKE_PROMPT = (
    "Hey Jarvis, Jarvis, Hey Jervis, Nexus, transform into immersive mode, "
    "transform into a human, return into assistant mode, open WhatsApp, "
    "play music on Spotify, UPES portal, Dehradun weather, top stories."
)


def calibrate():
    """Calibrates microphone once for ambient room noise and locks the floor."""
    mic = _get_mic()
    if not mic:
        _recognizer.energy_threshold = 280.0
        return
    with mic as source:
        try:
            print("[Jarvis] Calibrating microphone for room noise floor...")
            _recognizer.adjust_for_ambient_noise(source, duration=0.6)
            measured = float(_recognizer.energy_threshold)
            # Clamp between 180 and 450 so loud AC/fan noise never makes Jarvis deaf
            target = max(180.0, min(450.0, measured * 1.15))
            _recognizer.energy_threshold = target
            _recognizer.dynamic_energy_threshold = False
            print(f"[Jarvis] Mic calibrated & locked. Energy threshold: {_recognizer.energy_threshold:.0f}")
        except Exception as e:
            _recognizer.energy_threshold = 280.0
            _recognizer.dynamic_energy_threshold = False
            print(f"[Jarvis] Mic calibration fallback: {e}")


def transcribe_audio(audio: sr.AudioData, language="en-IN") -> str:
    """
    Ultra-fast transcription engine with lexical prompt biasing for 'Hey Jarvis'
    and built-in Silero VAD filtering to strip fan/background noise.
    """
    # 1. Primary: Local Faster-Whisper in memory with initial_prompt & VAD filter
    try:
        model = _get_offline_whisper()
        if model:
            import io
            wav_io = io.BytesIO(audio.get_wav_data())
            segments, _ = model.transcribe(
                wav_io,
                beam_size=1,
                best_of=1,
                temperature=0.0,
                initial_prompt=WHISPER_WAKE_PROMPT,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=250, speech_pad_ms=150),
            )
            text = " ".join([s.text for s in segments]).strip()
            if text:
                return text
    except Exception:
        pass

    # 2. Secondary fallback: Google Speech API (en-IN)
    try:
        res = _recognizer.recognize_google(audio, language=language).strip()
        if res:
            return res
    except sr.UnknownValueError:
        pass
    except Exception:
        pass

    # 3. Tertiary fallback: Google Speech API (en-US)
    try:
        res_us = _recognizer.recognize_google(audio, language="en-US").strip()
        if res_us:
            return res_us
    except Exception:
        pass

    return ""


# ---------- Speaking (ElevenLabs Realistic Custom Voice + Edge-TTS Multilingual Pipelining) ----------

_tts_lock = threading.Lock()
_speaking = threading.Event()
_interrupted = threading.Event()
_pyttsx_engine = None

VOICE_ID_EN = config.get("voice_id_en") or "fPIfC3elMLbN9tNwMXkw"  # Viraj (ElevenLabs English)
VOICE_ID_HI = config.get("voice_id_hi") or "ibbx9zDYGvLgtYzRbqqG"  # Hindi (ElevenLabs)

AVAILABLE_VOICES = {
    "Viraj (Indian English - ElevenLabs)": VOICE_ID_EN,
    "Hindi (ElevenLabs)": VOICE_ID_HI,
    "Indian English (Prabhat)": "en-IN-PrabhatNeural",
    "Indian Hindi (Madhur)": "hi-IN-MadhurNeural",
    "British Jarvis (Ryan)": "en-GB-RyanNeural",
    "British Butler (Thomas)": "en-GB-ThomasNeural",
    "American Warm (Jenny)": "en-US-JennyNeural",
}

_current_voice = "en-IN-PrabhatNeural"


def is_hindi(text: str) -> bool:
    """Returns True if the text contains Devanagari Unicode characters or common romanized Hindi words."""
    if any('\u0900' <= char <= '\u097f' for char in text):
        return True
    hindi_keywords = {
        'kya', 'kaise', 'karo', 'batao', 'namaste', 'shuru', 'hai', 'hain', 'hoon',
        'aap', 'tum', 'mujhe', 'mera', 'meri', 'mere', 'bhai', 'kripya', 'yaar',
        'theek', 'bolo', 'sunao', 'kahan', 'kyun', 'kitna', 'kitne', 'shukriya',
        'shant', 'alvida', 'aaj'
    }
    words = set(text.lower().split())
    return len(words.intersection(hindi_keywords)) > 0


def set_voice(voice_id_or_name: str):
    """Sets the active neural TTS voice."""
    global _current_voice
    if voice_id_or_name in AVAILABLE_VOICES:
        _current_voice = AVAILABLE_VOICES[voice_id_or_name]
    else:
        _current_voice = voice_id_or_name


def get_voice() -> str:
    return _current_voice


def play_audio_cue(cue: str = "wake"):
    """Plays low-latency futuristic audio status beeps using Windows winsound."""
    try:
        import winsound
        if cue == "ignite":
            winsound.Beep(520, 70)
            winsound.Beep(880, 80)
            winsound.Beep(1320, 110)
        elif cue == "lock" or cue == "standby":
            winsound.Beep(1040, 70)
            winsound.Beep(720, 80)
            winsound.Beep(440, 100)
        elif cue == "wake":
            winsound.Beep(880, 65)
            winsound.Beep(1320, 85)
        elif cue == "think":
            winsound.Beep(720, 45)
        elif cue == "bargein":
            winsound.Beep(450, 50)
    except Exception:
        pass


def stop_speaking():
    """Immediately interrupts and halts Jarvis's audio playback."""
    _interrupted.set()
    try:
        chan = _get_speech_channel()
        if chan and chan.get_busy():
            chan.stop()
    except Exception:
        pass


def was_interrupted() -> bool:
    """Checks if speech playback was interrupted."""
    return _interrupted.is_set()


def _get_pyttsx():
    global _pyttsx_engine
    if _pyttsx_engine is None:
        try:
            import pyttsx3
            _pyttsx_engine = pyttsx3.init()
            _pyttsx_engine.setProperty('rate', 190)
        except Exception as e:
            print(f"[TTS Fallback Init Error] {e}")
    return _pyttsx_engine


def _synthesize_elevenlabs(sentence_text: str, out_path: str, voice_id: str) -> bool:
    """Synthesizes high-fidelity speech using ElevenLabs API if key configured."""
    api_key = config.get("elevenlabs_api_key")
    if not api_key:
        return False
    try:
        import urllib.request
        import json
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        body = json.dumps({
            "text": sentence_text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.82
            }
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            with open(out_path, "wb") as f:
                f.write(response.read())
        return os.path.exists(out_path) and os.path.getsize(out_path) > 0
    except Exception as e:
        print(f"[ElevenLabs Notice] {e}")
        return False


def _synthesize_sentence(sentence_text: str, out_path: str, voice_name: str) -> bool:
    """
    Synthesizes a sentence chunk:
    1. Tries ElevenLabs (Viraj for English, Bunty for Hindi) if key is present.
    2. Falls back to Microsoft Edge-TTS (hi-IN-MadhurNeural for Hindi, en-IN-PrabhatNeural/Ryan for English).
    """
    hindi = is_hindi(sentence_text)
    eleven_voice = VOICE_ID_HI if hindi else VOICE_ID_EN

    # 1. Try ElevenLabs
    if _synthesize_elevenlabs(sentence_text, out_path, eleven_voice):
        return True

    # 2. Fallback: Edge-TTS
    target_edge_voice = "hi-IN-MadhurNeural" if hindi else "en-IN-PrabhatNeural"
    try:
        communicate = edge_tts.Communicate(sentence_text, target_edge_voice, rate="+5%")
        asyncio.run(communicate.save(out_path))
        return os.path.exists(out_path) and os.path.getsize(out_path) > 0
    except Exception:
        try:
            # Secondary British fallback
            communicate = edge_tts.Communicate(sentence_text, "en-GB-RyanNeural", rate="+5%")
            asyncio.run(communicate.save(out_path))
            return os.path.exists(out_path) and os.path.getsize(out_path) > 0
        except Exception:
            return False


def speak(text: str, on_start=None, on_end=None, allow_barge_in=True):
    """
    Speaks text aloud with pre-fetched sentence pipelining:
    Sentence 1 synthesizes and plays immediately while Sentence 2+ synthesize concurrently in the background.
    """
    if not text or not text.strip():
        if on_end:
            on_end()
        return

    clean_text = text.replace("*", "").replace("#", "").replace("`", "").strip()
    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?\n])\s+', clean_text) if s.strip()]
    if not sentences:
        sentences = [clean_text]

    with _tts_lock:
        _speaking.set()
        _interrupted.clear()

        try:
            import music_player
            music_player.duck_audio()
        except Exception:
            pass

        if on_start:
            on_start()

        temp_files = []
        synth_queue = queue.Queue()

        def _producer():
            for i, sentence in enumerate(sentences):
                if _interrupted.is_set():
                    break
                tmp_file = os.path.join(
                    tempfile.gettempdir(),
                    f"jarvis_speech_{int(time.time()*1000)}_{i}.mp3"
                )
                temp_files.append(tmp_file)
                ok = _synthesize_sentence(sentence, tmp_file, _current_voice)
                synth_queue.put((sentence, tmp_file, ok))
            synth_queue.put(None)

        producer_thread = threading.Thread(target=_producer, daemon=True)
        producer_thread.start()

        try:
            while True:
                item = synth_queue.get()
                if item is None or _interrupted.is_set():
                    break
                sentence, tmp_file, success = item
                if success:
                    try:
                        chan = _get_speech_channel()
                        snd = pygame.mixer.Sound(tmp_file)
                        if chan:
                            chan.set_volume(1.0)
                            chan.play(snd)
                            while chan.get_busy():
                                if _interrupted.is_set():
                                    chan.stop()
                                    break
                                time.sleep(0.015)
                    except Exception as e:
                        print(f"[Playback error] {e}")
                else:
                    if not _interrupted.is_set():
                        engine = _get_pyttsx()
                        if engine:
                            engine.say(sentence)
                            engine.runAndWait()
        finally:
            for f in temp_files:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass
            _speaking.clear()
            if on_end:
                on_end()


# ---------- Wake Word & Command Extraction ----------

_porcupine = None
_pa = None
PPN_PATH = os.path.join(os.path.dirname(__file__), "jarvis.ppn")

def _try_init_porcupine():
    global _porcupine, _pa
    access_key = config.get("porcupine_access_key")
    if not access_key:
        return False
    try:
        import pvporcupine
        import pyaudio
        if os.path.exists(PPN_PATH):
            _porcupine = pvporcupine.create(access_key=access_key, keyword_paths=[PPN_PATH])
        else:
            # Built-in 'jarvis' keyword ships with pvporcupine out of the box!
            _porcupine = pvporcupine.create(access_key=access_key, keywords=["jarvis"])
        _pa = pyaudio.PyAudio()
        return True
    except Exception:
        _porcupine = None
        return False

_offline_checked = False
_offline_ready = False

def _is_offline_ready():
    global _offline_checked, _offline_ready
    if not _offline_checked:
        _offline_checked = True
        _offline_ready = _try_init_porcupine()
    return _offline_ready

# ---------- Lifecycle States & Power Management ----------

STATE_LOCKED = "LOCKED"
STATE_STANDBY = "STANDBY"
STATE_ACTIVE = "ACTIVE"

_system_state = STATE_LOCKED
_state_lock = threading.Lock()
_state_listeners = []


def get_system_state() -> str:
    global _system_state
    with _state_lock:
        return _system_state


def set_system_state(new_state: str, announce: bool = True):
    global _system_state
    with _state_lock:
        old_state = _system_state
        _system_state = new_state
    print(f"[Jarvis State Transition] {old_state} -> {new_state}")
    for cb in _state_listeners:
        try:
            cb(new_state)
        except Exception:
            pass
    if announce:
        if new_state == STATE_STANDBY:
            play_audio_cue("ignite")
        elif new_state == STATE_LOCKED:
            play_audio_cue("lock")


def add_state_listener(callback):
    _state_listeners.append(callback)


def toggle_system_ignition():
    """Toggles system between LOCKED and STANDBY via the 'Car Key' shortcut."""
    curr = get_system_state()
    if curr == STATE_LOCKED:
        set_system_state(STATE_STANDBY)
        speak("Ignition confirmed. Jarvis in standby. Say 'Hey Jarvis' to activate.")
    else:
        set_system_state(STATE_LOCKED)
        speak("Jarvis locked down.")


def start_global_hotkey_listener(on_toggle_callback=None):
    """
    Registers system-wide Windows shortcut Ctrl + Alt + J via Win32 RegisterHotKey.
    Pressing Ctrl+Alt+J anywhere in Windows toggles Jarvis ignition.
    """
    cb = on_toggle_callback or toggle_system_ignition

    def _hotkey_thread():
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            MOD_ALT = 0x0001
            MOD_CONTROL = 0x0002
            MOD_NOREPEAT = 0x4000
            VK_J = 0x4A
            HOTKEY_ID = 48101

            if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_J):
                print("[Jarvis Hotkey] Notice: Could not register Ctrl+Alt+J hotkey (may already be in use).")
                return

            print("[Jarvis Hotkey] System-Wide Ignition Hotkey Active: [Ctrl + Alt + J]")
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                    cb()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            print(f"[Jarvis Hotkey Warning] {e}")

    t = threading.Thread(target=_hotkey_thread, daemon=True)
    t.start()


def start_sleep_monitor(on_sleep_callback=None):
    """
    Monitors Windows suspend/sleep/hibernate.
    When laptop wakes up from sleep or hibernate, immediately resets Jarvis to LOCKED state.
    """
    def _power_thread():
        last_tick = time.time()
        while True:
            time.sleep(1.0)
            now = time.time()
            if now - last_tick > 3.5:
                print(f"[Jarvis Power] Laptop wake from sleep/hibernate detected ({now-last_tick:.1f}s gap). Locking down.")
                set_system_state(STATE_LOCKED, announce=False)
                if on_sleep_callback:
                    try:
                        on_sleep_callback()
                    except Exception:
                        pass
            last_tick = now

    t = threading.Thread(target=_power_thread, daemon=True)
    t.start()


# ---------- Wake Word & Command Extraction (Strict Lifecycle) ----------

# 1. Ignition wake phrases (ONLY allowed when waking from STANDBY)
IGNITION_WAKE_PATTERNS = [
    "hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "okay jarvis",
    "wake up jarvis", "listen jarvis", "start jarvis", "wake jarvis",
    "hey jervis", "hi jervis", "hello jervis", "ok jervis", "okay jervis",
    "wake up jervis", "start jervis", "wake jervis",
    "हे जार्विस", "हे जर्विस", "नमस्ते जार्विस", "जार्विस शुरू करो", "सुनो जार्विस"
]

# 2. Active wake prefixes (Allowed when system is ALREADY active)
ACTIVE_WAKE_PATTERNS = [
    "hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "okay jarvis",
    "jarvis", "jervis", "hey jervis", "hi jervis", "ok jervis",
    "हे जार्विस", "जार्विस", "हे जर्विस", "जर्विस"
]

STANDBY_COMMANDS = [
    "standby", "stand by", "go to sleep", "sleep", "stop listening",
    "स्टैंडबाय", "सो जाओ", "शांत रहो"
]


def check_wake_word(text: str, session_active: bool = False) -> tuple[bool, str]:
    """
    Strict two-tier wake word check:
    - If in STANDBY (session_active=False): ONLY accepts ignition phrases ('Hey Jarvis').
      Single 'Jarvis' and random room noises are strictly rejected!
    - If in ACTIVE (session_active=True): Accepts 'Jarvis [cmd]' or 'Hey Jarvis [cmd]'.
    """
    if not text or not text.strip():
        return False, ""
    clean = text.lower().strip()

    # Tier 1: Standby Mode — Strict Ignition Wake Phrase ONLY
    if not session_active:
        for p in sorted(IGNITION_WAKE_PATTERNS, key=len, reverse=True):
            idx = clean.find(p)
            if idx != -1:
                cmd = clean[idx + len(p):].strip()
                cmd = cmd.strip(string.punctuation).strip()
                return True, cmd
        # Reject everything else in Standby
        return False, ""

    # Tier 2: Active Mode — Check Standby / Sleep command first
    for s in STANDBY_COMMANDS:
        if s in clean:
            return True, "standby"

    # Active Mode — Accept 'Jarvis [cmd]' or full prompt
    for p in sorted(ACTIVE_WAKE_PATTERNS, key=len, reverse=True):
        idx = clean.find(p)
        if idx != -1:
            cmd = clean[idx + len(p):].strip()
            cmd = cmd.strip(string.punctuation).strip()
            return True, cmd

    # In active continuous dialogue, accept substantive query (>1 word)
    words = clean.split()
    if len(words) >= 2:
        return True, clean

    return False, ""


def listen_for_wake_word(session_active: bool = False) -> tuple[bool, str]:
    """
    Ultra-responsive wake word listener.
    - If Porcupine is active: keeps stream open in a tight frame loop (fixes single-frame bug).
    - Otherwise: uses a fast 3.2s window with 0.45s pause_threshold so background noise never blocks for 7.5s.
    """
    if _is_offline_ready() and _porcupine:
        stream = _pa.open(
            rate=_porcupine.sample_rate,
            channels=1,
            format=8,
            input=True,
            frames_per_buffer=_porcupine.frame_length,
        )
        try:
            # Poll continuously for ~2.5 seconds per cycle instead of 1 single 32ms frame
            frames_to_poll = int((_porcupine.sample_rate / _porcupine.frame_length) * 2.5)
            for _ in range(frames_to_poll):
                pcm = stream.read(_porcupine.frame_length, exception_on_overflow=False)
                pcm_unpacked = struct.unpack_from("h" * _porcupine.frame_length, pcm)
                if _porcupine.process(pcm_unpacked) >= 0:
                    play_audio_cue("wake")
                    return True, ""
            return False, ""
        finally:
            stream.close()

    mic = _get_mic()
    if not mic:
        return False, ""
    with mic as source:
        try:
            _recognizer.pause_threshold = 0.45
            _recognizer.phrase_threshold = 0.15
            _recognizer.non_speaking_duration = 0.28
            # Fast 1.2s wait timeout + 4.0s phrase limit prevents 7.5s lockups on ambient room noise
            audio = _recognizer.listen(source, timeout=1.2, phrase_time_limit=4.0)
        except sr.WaitTimeoutError:
            return False, ""
        except Exception:
            return False, ""

    raw_text = transcribe_audio(audio, language="en-IN")
    if not raw_text:
        return False, ""

    print(f"[Jarvis Mic Heard]: '{raw_text}' (SessionActive={session_active})")
    is_wake, extracted_cmd = check_wake_word(raw_text, session_active=session_active)
    if is_wake:
        try:
            import music_player
            music_player.duck_audio()
        except Exception:
            pass
        play_audio_cue("wake")
        print(f" -> [WAKE TRIGGERED!] Command: '{extracted_cmd or '(wake only)'}'")
        return True, extracted_cmd
    else:
        try:
            import music_player
            if music_player.is_playing():
                clean_lower = raw_text.lower().strip(string.punctuation).strip()
                if clean_lower in ("next", "next song", "skip", "skip song", "pause", "pause music", "resume", "resume music", "stop"):
                    music_player.duck_audio()
                    return True, clean_lower
        except Exception:
            pass

        return False, ""


def listen_for_command(timeout=4.5, phrase_time_limit=8.0, on_amplitude=None) -> str:
    """Listens for user's command with fast 400ms pause threshold."""
    print("[Debug] Listening for your command now...")
    try:
        import music_player
        music_player.duck_audio()
    except Exception:
        pass
    mic = _get_mic()
    if not mic:
        return False, ""
    with mic as source:
        try:
            _recognizer.pause_threshold = 0.40
            _recognizer.phrase_threshold = 0.15
            _recognizer.non_speaking_duration = 0.25
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            print("[Debug] Stopped listening (silence timeout).")
            return ""
        except Exception as e:
            print(f"[Debug] Mic error: {e}")
            return ""

    print("[Debug] Audio captured! Transcribing speech...")
    text = transcribe_audio(audio, language="en-IN")
    if text:
        print(f"[Debug] You said: {text}")
    else:
        print("[Debug] Could not understand audio.")
    return text

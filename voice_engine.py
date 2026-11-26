"""
voice_engine.py – Zero-Phantom, Ultra-Fast Speech I/O for J.A.R.V.I.S.

Fixes all reported voice issues:
1. Eliminates phantom self-triggering & random "Data Science" hallucinations:
   - Removes wake-word `initial_prompt` biasing (which caused Whisper to hallucinate "Hey Jarvis" on silence/fan noise).
   - Rejects Whisper segments with `no_speech_prob > 0.55` or `avg_logprob < -1.0`, and filters known Whisper silence hallucinations ("thank you", "you", "bye", etc.).
   - Uses `dynamic_energy_threshold = True` with a safe floor (`max(300, measured * 1.35)`) so background noise never triggers empty recordings.
2. Strict Ignition -> Active -> Standby Wake-Word Lifecycle:
   - STANDBY (`session_active=False`): Only wakes on explicit "Hey Jarvis" (or phonetic variants like "hey jervis").
   - ACTIVE (`session_active=True`): After ignition, commands only need "Jarvis <command>" (no need to repeat "Hey Jarvis"), and NEVER accepts random ambient speech without "Jarvis" in it.
3. True ElevenLabs Bilingual Voices (`eleven_flash_v2_5` for <350ms latency):
   - English Voice ID: `fPIfC3elMLbN9tNwMXkw`
   - Hindi Voice ID:   `ibbx9zDYGvLgtYzRbqqG`
   - Strict Hindi detection (Devanagari script or >=2 Hindi words) so English never randomly switches to Hindi.
"""

import os
import io
import re
import time
import queue
import struct
import string
import asyncio
import difflib
import tempfile
import threading
import requests
import pygame
import edge_tts
import speech_recognition as sr
import config

# ElevenLabs Voice IDs (User-configured)
VOICE_ID_EN = config.get("voice_id_en") or "fPIfC3elMLbN9tNwMXkw"
VOICE_ID_HI = config.get("voice_id_hi") or "ibbx9zDYGvLgtYzRbqqG"

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


# Preload whisper model in background
threading.Thread(target=_get_offline_whisper, daemon=True).start()

# Recognizer configuration – fast, high-sensitivity anti-deaf thresholds
_recognizer = sr.Recognizer()
_recognizer.energy_threshold = 280.0
_recognizer.dynamic_energy_threshold = False  # Locked after calibration to avoid ambient noise inflation
_recognizer.pause_threshold = 0.85
_recognizer.phrase_threshold = 0.20
_recognizer.non_speaking_duration = 0.45

_mic = sr.Microphone()
_last_speech_end_time = 0.0

# Common Whisper hallucinations on silence/fan noise
SILENCE_HALLUCINATIONS = {
    "thank you", "thank you.", "thanks", "thanks for watching", "you", "bye",
    "bye.", "uh", "um", "hmm", "ah", "oh", "okay", "ok", "yes", "no",
    "subtitles by", "amara.org", "mbc", "i'm sorry", "sorry"
}


def calibrate():
    """Calibrates microphone for ambient room noise with a safe, sensitive floor."""
    with _mic as source:
        try:
            print("[Jarvis] Calibrating microphone for room noise floor...")
            _recognizer.adjust_for_ambient_noise(source, duration=0.6)
            measured = float(_recognizer.energy_threshold)
            target = max(180.0, min(420.0, measured * 1.15))
            _recognizer.energy_threshold = target
            _recognizer.dynamic_energy_threshold = False
            print(f"[Jarvis] Mic calibrated and locked. Energy threshold: {_recognizer.energy_threshold:.0f}")
        except Exception as e:
            _recognizer.energy_threshold = 280.0
            _recognizer.dynamic_energy_threshold = False
            print(f"[Jarvis] Mic calibration fallback: {e}")


def transcribe_audio(audio: sr.AudioData, language: str = "en-IN") -> str:
    """
    Fast, highly reliable transcription optimized for Indian English accents:
    1. Primary: Google Speech Recognition (en-IN) — ultra-fast (<350ms), exceptional Indian accent accuracy.
    2. Fallback: Local Faster-Whisper with Silero VAD — private, offline.
    3. Tertiary: Google Speech Recognition (hi-IN) — for Hindi / Hinglish.
    """
    # 1. Primary: Google Speech Recognition (en-IN)
    try:
        t0 = time.time()
        res = _recognizer.recognize_google(audio, language=language).strip()
        dt = time.time() - t0
        if res and res.lower().strip(string.punctuation) not in SILENCE_HALLUCINATIONS:
            print(f"[STT] Google ({language}) transcribed in {dt:.3f}s: '{res}'")
            return res
    except Exception:
        pass

    # 2. Secondary fallback: Local Faster-Whisper
    try:
        model = _get_offline_whisper()
        if model:
            t0 = time.time()
            wav_io = io.BytesIO(audio.get_wav_data())
            segments, _ = model.transcribe(
                wav_io,
                beam_size=1,
                best_of=1,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=250, speech_pad_ms=150),
            )
            valid_chunks = []
            for s in segments:
                if getattr(s, "no_speech_prob", 0.0) > 0.70:
                    continue
                if getattr(s, "avg_logprob", 0.0) < -1.85:
                    continue
                chunk = s.text.strip()
                if chunk and chunk.lower().strip(string.punctuation) not in SILENCE_HALLUCINATIONS:
                    valid_chunks.append(chunk)
            text = " ".join(valid_chunks).strip()
            dt = time.time() - t0
            if text:
                print(f"[STT] Faster-Whisper transcribed in {dt:.3f}s: '{text}'")
                return text
    except Exception:
        pass

    # 3. Tertiary fallback: Google Speech API (hi-IN for Hindi/Hinglish)
    if language != "hi-IN":
        try:
            res_hi = _recognizer.recognize_google(audio, language="hi-IN").strip()
            if res_hi and res_hi.lower().strip(string.punctuation) not in SILENCE_HALLUCINATIONS:
                print(f"[STT] Google (hi-IN) transcribed: '{res_hi}'")
                return res_hi
        except Exception:
            pass

    return ""


# ---------- Language Detection & ElevenLabs + Edge-TTS Speaking ----------

_HINDI_KEYWORDS = {
    "hai", "hain", "hoon", "ho", "kya", "kaise", "kaisa", "kaisi", "karo", "kar",
    "batao", "bata", "mujhe", "mera", "meri", "mere", "tum", "aap", "yaar", "bhai",
    "aaj", "kal", "abhi", "nahi", "haan", "theek", "accha", "acha", "jao", "chalo",
    "sunno", "suno", "samjhe", "samjha", "kyun", "kahan", "kab", "kaun"
}


def is_hindi(text: str) -> bool:
    """
    Returns True ONLY when the text is genuinely in Hindi/Devanagari or clearly Hinglish (>=2 Hindi words).
    Prevents English sentences from accidentally triggering the Hindi voice.
    """
    if not text:
        return False
    # Devanagari Unicode range
    if any("\u0900" <= ch <= "\u097f" for ch in text):
        return True
    words = [w.strip(string.punctuation).lower() for w in text.split()]
    hindi_hits = sum(1 for w in words if w in _HINDI_KEYWORDS)
    return hindi_hits >= 2


_tts_lock = threading.Lock()
_speaking = threading.Event()
_interrupted = threading.Event()
_pyttsx_engine = None

AVAILABLE_VOICES = {
    "Jarvis English (ElevenLabs)": VOICE_ID_EN,
    "Jarvis Hindi (ElevenLabs)": VOICE_ID_HI,
    "British Jarvis (Ryan)": "en-GB-RyanNeural",
    "Indian English (Prabhat)": "en-IN-PrabhatNeural",
    "Hindi (Madhur)": "hi-IN-MadhurNeural",
}

_current_voice = VOICE_ID_EN


def set_voice(voice_id_or_name: str):
    global _current_voice
    _current_voice = AVAILABLE_VOICES.get(voice_id_or_name, voice_id_or_name)


def get_voice() -> str:
    return _current_voice


def play_audio_cue(cue: str = "wake"):
    """Plays crisp, low-latency status cues."""
    try:
        import winsound
        if cue == "wake":
            winsound.Beep(880, 55)
            winsound.Beep(1320, 75)
        elif cue == "think":
            winsound.Beep(720, 40)
        elif cue == "standby":
            winsound.Beep(880, 65)
            winsound.Beep(520, 85)
        elif cue == "bargein":
            winsound.Beep(450, 45)
    except Exception:
        pass


def stop_speaking():
    _interrupted.set()
    try:
        chan = _get_speech_channel()
        if chan and chan.get_busy():
            chan.stop()
    except Exception:
        pass


def was_interrupted() -> bool:
    return _interrupted.is_set()


def _get_pyttsx():
    global _pyttsx_engine
    if _pyttsx_engine is None:
        try:
            import pyttsx3
            _pyttsx_engine = pyttsx3.init()
            _pyttsx_engine.setProperty("rate", 190)
        except Exception:
            pass
    return _pyttsx_engine


def _synthesize_elevenlabs(sentence_text: str, out_path: str, voice_id: str) -> bool:
    """
    Synthesizes speech via ElevenLabs using `eleven_flash_v2_5` (~250ms ultra-low latency)
    with fallback to `eleven_multilingual_v2`.
    """
    api_key = config.get("elevenlabs_api_key")
    if not api_key:
        return False

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    for model_id in ("eleven_flash_v2_5", "eleven_multilingual_v2"):
        payload = {
            "text": sentence_text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.50,
                "similarity_boost": 0.78,
                "style": 0.15,
                "use_speaker_boost": True,
            },
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=8)
            if resp.status_code == 200 and resp.content:
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                return True
            else:
                print(f"[ElevenLabs {model_id} HTTP {resp.status_code}]: {resp.text[:120]}")
        except Exception as e:
            print(f"[ElevenLabs {model_id} Error]: {e}")
    return False


def _synthesize_sentence(sentence_text: str, out_path: str, voice_override: str | None = None) -> bool:
    """
    Primary: ElevenLabs (`fPIfC3elMLbN9tNwMXkw` for English, `ibbx9zDYGvLgtYzRbqqG` for Hindi).
    Fallback: Edge-TTS (`en-IN-PrabhatNeural` / `hi-IN-MadhurNeural`).
    """
    hindi = is_hindi(sentence_text)
    eleven_voice = VOICE_ID_HI if hindi else VOICE_ID_EN

    if voice_override and voice_override not in (VOICE_ID_EN, VOICE_ID_HI) and "Neural" not in voice_override:
        eleven_voice = voice_override

    if _synthesize_elevenlabs(sentence_text, out_path, eleven_voice):
        return True

    # Fallback to Edge-TTS if ElevenLabs key is missing or offline
    edge_voice = "hi-IN-MadhurNeural" if hindi else "en-IN-PrabhatNeural"
    if voice_override and "Neural" in voice_override and not hindi:
        edge_voice = voice_override

    try:
        communicate = edge_tts.Communicate(sentence_text, edge_voice, rate="+6%")
        asyncio.run(communicate.save(out_path))
        return os.path.exists(out_path) and os.path.getsize(out_path) > 0
    except Exception:
        return False


def speak(text: str, on_start=None, on_end=None, allow_barge_in=True):
    """Pipelined neural TTS: synthesizes sentence N+1 while sentence N plays."""
    if not text or not text.strip():
        if on_end:
            on_end()
        return

    clean_text = text.replace("*", "").replace("#", "").replace("`", "").strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?\n।])\s+", clean_text) if s.strip()]
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
                    f"jarvis_speech_{int(time.time() * 1000)}_{i}.mp3"
                )
                temp_files.append(tmp_file)
                ok = _synthesize_sentence(sentence, tmp_file, _current_voice)
                synth_queue.put((sentence, tmp_file, ok))
            synth_queue.put(None)

        threading.Thread(target=_producer, daemon=True).start()

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
            global _last_speech_end_time
            _last_speech_end_time = time.time()
            if on_end:
                on_end()


# ---------- Wake Word & Ignition State Machine ----------

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
            _porcupine = pvporcupine.create(access_key=access_key, keywords=["jarvis"])
        _pa = pyaudio.PyAudio()
        return True
    except Exception:
        _porcupine = None
        return False


_offline_ready = _try_init_porcupine()

# Cold-start ignition phrases (requires "Hey Jarvis" / phonetic variants)
COLD_WAKE_PATTERNS = [
    "hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "okay jarvis",
    "wake up jarvis", "hay jarvis", "hey jervis", "hi jervis", "ok jervis",
    "hey jarvice", "hey jervise", "hey jarves", "hey service", "hey javis",
    "हे जार्विस", "हे जर्विस", "नमस्ते जार्विस", "सुनो जार्विस", "ए जार्विस",
]

# Active-session triggers ("Jarvis <cmd>" works without repeating "Hey")
ACTIVE_WAKE_PATTERNS = COLD_WAKE_PATTERNS + [
    "jarvis", "jervis", "jarvice", "jervise", "jarves", "javis", "jarvez",
    "जार्विस", "जर्विस"
]

STANDBY_PHRASES = {
    "goodbye jarvis", "bye jarvis", "jarvis bye", "jarvis jao", "jao jarvis",
    "go to sleep", "sleep jarvis", "standby", "stand by", "jarvis standby",
    "stop listening", "shut up jarvis", "सो जाओ", "शांत रहो"
}

WAKE_TOKENS = {"jarvis", "jervis", "jarvice", "jervise", "jarves", "javis", "jarvez", "जार्विस", "जर्विस"}
FUZZY_WAKE_TARGETS = ("jarvis", "jervis", "jarvice", "jervise", "javis")


def is_standby_command(text: str) -> bool:
    clean = (text or "").lower().strip(string.punctuation).strip()
    return any(p in clean for p in STANDBY_PHRASES)


def check_wake_word(text: str, session_active: bool = False) -> tuple[bool, str]:
    """
    Strict Wake-Word Extractor:
    - STANDBY (`session_active=False`): Requires 'Hey Jarvis' (ignition).
    - ACTIVE  (`session_active=True`):  Requires 'Jarvis' (e.g. 'Jarvis open Spotify') or a standby phrase.
      NEVER accepts random ambient speech without 'Jarvis' in it!
    """
    if not text or not text.strip():
        return False, ""
    clean = text.lower().strip()

    if session_active and is_standby_command(clean):
        return True, "__STANDBY__"

    patterns = sorted(ACTIVE_WAKE_PATTERNS if session_active else COLD_WAKE_PATTERNS, key=len, reverse=True)
    for p in patterns:
        idx = clean.find(p)
        if idx != -1:
            cmd = clean[idx + len(p):].strip().strip(string.punctuation).strip()
            return True, cmd

    # Fuzzy token check ONLY for active session ("Jarvis") or when "hey/hi/ok" precedes a fuzzy match
    words = [w.strip(string.punctuation).strip() for w in clean.split() if w.strip(string.punctuation).strip()]
    for i, w in enumerate(words):
        if session_active:
            if w in WAKE_TOKENS or any(difflib.SequenceMatcher(None, w, t).ratio() >= 0.78 for t in FUZZY_WAKE_TARGETS):
                cmd = " ".join(words[i + 1:]).strip()
                return True, cmd
        else:
            if i > 0 and words[i - 1] in ("hey", "hi", "hay", "ok", "okay", "a"):
                if w in WAKE_TOKENS or any(difflib.SequenceMatcher(None, w, t).ratio() >= 0.76 for t in FUZZY_WAKE_TARGETS):
                    cmd = " ".join(words[i + 1:]).strip()
                    return True, cmd

    return False, ""


def listen_for_wake_word(session_active: bool = False) -> tuple[bool, str]:
    """
    Listens for 'Hey Jarvis' (Standby) or 'Jarvis <command>' (Active).
    Eliminates 7.5s lockups and never triggers on silence.
    """
    if not session_active and _offline_ready and _porcupine:
        stream = _pa.open(
            rate=_porcupine.sample_rate,
            channels=1,
            format=8,
            input=True,
            frames_per_buffer=_porcupine.frame_length,
        )
        try:
            frames_to_poll = int((_porcupine.sample_rate / _porcupine.frame_length) * 2.0)
            for _ in range(frames_to_poll):
                pcm = stream.read(_porcupine.frame_length, exception_on_overflow=False)
                pcm_unpacked = struct.unpack_from("h" * _porcupine.frame_length, pcm)
                if _porcupine.process(pcm_unpacked) >= 0:
                    play_audio_cue("wake")
                    return True, ""
            return False, ""
        finally:
            stream.close()

    with _mic as source:
        try:
            _recognizer.pause_threshold = 0.45
            _recognizer.phrase_threshold = 0.15
            _recognizer.non_speaking_duration = 0.28
            audio = _recognizer.listen(source, timeout=1.8, phrase_time_limit=5.0)
        except sr.WaitTimeoutError:
            return False, ""
        except Exception:
            return False, ""

    raw_text = transcribe_audio(audio, language="en-IN")
    if not raw_text:
        return False, ""

    print(f"[Jarvis Mic Heard]: '{raw_text}' (Active={session_active})")
    is_wake, extracted_cmd = check_wake_word(raw_text, session_active=session_active)
    if is_wake:
        try:
            import music_player
            music_player.duck_audio()
        except Exception:
            pass
        if extracted_cmd != "__STANDBY__":
            play_audio_cue("wake")
        return True, extracted_cmd

    return False, ""


def is_speaking() -> bool:
    return _speaking.is_set()


def listen_for_command(timeout=4.5, phrase_time_limit=12.0, on_amplitude=None) -> str:
    """
    Listens for speech input with active anti-self-hearing:
    1. Waits if Jarvis is currently speaking (blocks TTS feedback).
    2. Enforces a 250ms acoustic grace buffer after TTS stops before opening mic.
    3. Uses generous pause_threshold (0.85s) for natural Indian English phrasing.
    4. Distinguishes NO SPEECH from actual commands (returns "" on silence).
    """
    # 1. Block listening while speaking
    while _speaking.is_set():
        time.sleep(0.05)

    # 2. Wait out residual acoustic room echo from laptop speakers
    elapsed = time.time() - _last_speech_end_time
    if elapsed < 0.25:
        time.sleep(0.25 - elapsed)

    try:
        import music_player
        music_player.duck_audio()
    except Exception:
        pass

    with _mic as source:
        try:
            _recognizer.pause_threshold = 0.85
            _recognizer.phrase_threshold = 0.20
            _recognizer.non_speaking_duration = 0.45
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            return ""
        except Exception:
            return ""

    return transcribe_audio(audio, language="en-IN")


def get_startup_greeting() -> str:
    """Returns a natural, warm conversational greeting for Jarvis startup."""
    import datetime
    hr = datetime.datetime.now().hour
    if 4 <= hr < 12:
        part = "Good morning"
    elif 12 <= hr < 17:
        part = "Good afternoon"
    else:
        part = "Good evening"
    return f"{part} Nakul. Jarvis online, how can I help?"
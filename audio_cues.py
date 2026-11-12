"""
audio_cues.py — Studio-Quality Spatial Acoustic Feedback Engine for Jarvis 2.0.

Synthesizes elegant, harmonic sci-fi audio cues directly in memory using numpy
and pygame.mixer (modeled on Nexus Spatial OS and futuristic holographic HUDs).
Eliminates reliance on motherboard winsound beeps.
"""

import threading
import numpy as np

try:
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    _PYGAME_AVAILABLE = True
except Exception:
    _PYGAME_AVAILABLE = False

_CACHED_SOUNDS = {}

def _synthesize_tone(freq_start: float, freq_end: float, duration: float, volume: float = 0.35) -> object:
    """Synthesizes a smooth harmonic sine chirp with exponential decay envelope."""
    if not _PYGAME_AVAILABLE:
        return None
    try:
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)

        # Smooth frequency sweep
        if freq_start == freq_end:
            freqs = freq_start
        else:
            freqs = np.linspace(freq_start, freq_end, n_samples)
        
        # Phase integration
        phases = 2 * np.pi * np.cumsum(freqs) / sample_rate
        raw_wave = np.sin(phases)

        # Envelope: fast 5ms attack, exponential decay to prevent clicks
        attack_len = int(sample_rate * 0.005)
        envelope = np.ones(n_samples, dtype=np.float32)
        if attack_len > 0 and attack_len < n_samples:
            envelope[:attack_len] = np.linspace(0, 1, attack_len)
        decay = np.exp(-t * (4.5 / duration))
        envelope = envelope * decay * volume

        stereo = np.vstack((raw_wave * envelope, raw_wave * envelope)).T
        c_stereo = np.ascontiguousarray((stereo * 32767).astype(np.int16))
        return pygame.sndarray.make_sound(c_stereo)
    except Exception as e:
        print(f"[AudioCues] Synth error: {e}")
        return None

def _get_sound(cue_type: str):
    if cue_type in _CACHED_SOUNDS:
        return _CACHED_SOUNDS[cue_type]

    snd = None
    if cue_type == "wake":
        # Ascending dual-tone sci-fi chime (660Hz -> 880Hz)
        snd = _synthesize_tone(660, 880, 0.14, volume=0.32)
    elif cue_type == "listen":
        # Micro pulse chime confirming mic activation (950Hz)
        snd = _synthesize_tone(950, 1100, 0.09, volume=0.28)
    elif cue_type == "think":
        # Sub-harmonic low pulse (440Hz -> 380Hz)
        snd = _synthesize_tone(440, 380, 0.12, volume=0.22)
    elif cue_type == "confirm":
        # Affirmative spatial chord (750Hz -> 1000Hz)
        snd = _synthesize_tone(750, 1000, 0.16, volume=0.35)
    elif cue_type == "alert":
        # Notification reminder chime (880Hz -> 1180Hz)
        snd = _synthesize_tone(880, 1180, 0.22, volume=0.38)
    elif cue_type == "stop":
        # Descending power-down tone (520Hz -> 320Hz)
        snd = _synthesize_tone(520, 320, 0.15, volume=0.28)

    if snd:
        _CACHED_SOUNDS[cue_type] = snd
    return snd

def play(cue_type: str):
    """
    Plays an asynchronous spatial audio feedback cue without blocking the caller.
    Supported types: 'wake', 'listen', 'think', 'confirm', 'alert', 'stop'
    """
    def _play_async():
        try:
            snd = _get_sound(cue_type)
            if snd:
                snd.play()
            else:
                # Fallback to winsound
                import winsound
                if cue_type in ("wake", "listen"):
                    winsound.Beep(880, 60)
                elif cue_type == "confirm":
                    winsound.Beep(980, 80)
                elif cue_type == "alert":
                    winsound.Beep(1200, 120)
                elif cue_type == "stop":
                    winsound.Beep(440, 80)
                else:
                    winsound.Beep(600, 50)
        except Exception:
            pass

    threading.Thread(target=_play_async, daemon=True).start()

# Pre-synthesize core sounds on module import
try:
    for c in ("wake", "listen", "think", "confirm", "alert", "stop"):
        _get_sound(c)
except Exception:
    pass

if __name__ == "__main__":
    import time
    print("Testing spatial audio cues...")
    for cue in ("wake", "listen", "think", "confirm", "alert", "stop"):
        print(f"Playing cue: {cue}")
        play(cue)
        time.sleep(0.4)
    print("Test completed.")

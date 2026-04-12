"""
Simple audio tones for headless feedback.
Uses sounddevice + numpy — no extra dependencies.
"""

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100


def _beep(freq: float, duration: float, volume: float = 0.4) -> None:
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = (np.sin(2 * np.pi * freq * t) * volume).astype(np.float32)
    # Short fade-out to avoid a click at the end
    fade = min(int(SAMPLE_RATE * 0.02), len(wave))
    wave[-fade:] *= np.linspace(1.0, 0.0, fade)
    sd.play(wave, SAMPLE_RATE)
    sd.wait()


def play_listening_tone() -> None:
    """Two ascending tones — signals the assistant is now listening."""
    _beep(440, 0.12)
    _beep(880, 0.18)


def play_done_tone() -> None:
    """Single descending tone — signals the assistant is done and going back to sleep."""
    _beep(880, 0.12)
    _beep(440, 0.12)

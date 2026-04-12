"""
Wake word detection using faster-whisper.

Records short audio clips continuously and transcribes them.
Fires when the configured keyword (default: "pi") is heard.

Works on Mac (built-in mic) and Pi (XM5 HFP mic).
Shares the same WhisperModel instance as stt.py — loaded once.

Requirements:
  pip install faster-whisper sounddevice
"""

import queue
import numpy as np
import sounddevice as sd

import config
from audio.stt import _get_model, _transcribe

SAMPLE_RATE = 16000
CLIP_SAMPLES = SAMPLE_RATE * 3   # listen in 3-second windows


def wait_for_wake_word() -> None:
    """
    Block until the configured wake word keyword is heard.
    Transcribes 3-second audio windows until the keyword appears.
    """
    keyword = config.WAKE_WORD_KEYWORD.lower().strip()
    device = config.MIC_DEVICE

    # Pre-load model so first detection isn't slow
    _get_model()

    audio_q: queue.Queue[np.ndarray] = queue.Queue()

    def _callback(indata, frames, time, status):
        audio_q.put(indata[:, 0].copy())

    print(f"[wake_word] Waiting for '{keyword}'...", flush=True)

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=CLIP_SAMPLES,
        device=device,
        dtype="int16",
        channels=1,
        callback=_callback,
    ):
        while True:
            clip = audio_q.get()
            text = _transcribe(clip).lower()
            if not text:
                continue
            # Strip punctuation, then check if keyword phrase appears in transcript.
            # Works for both single words ("pi") and phrases ("hey there").
            clean = text.replace(",", "").replace(".", "").replace("?", "").replace("!", "")
            if keyword in clean:
                print(f"[wake_word] Heard: {text!r}", flush=True)
                return

"""
Speech-to-text using faster-whisper.

Records from the mic using energy-based VAD (starts on speech, stops on silence),
then transcribes with faster-whisper.

Works on Mac (built-in mic) and Pi (XM5 HFP mic).
Model is downloaded automatically from HuggingFace on first use.

Requirements:
  pip install faster-whisper sounddevice
"""

import queue
import numpy as np
import sounddevice as sd

import config

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1600       # 100 ms per chunk
SILENCE_CHUNKS = 15        # 1.5 s of silence → end of utterance
MAX_CHUNKS = 100           # 10 s hard cap

# Shared model instance — loaded once, reused across calls
_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        name = config.WHISPER_MODEL
        print(f"[stt] Loading Whisper model '{name}'...", flush=True)
        _model = WhisperModel(name, device="cpu", compute_type="int8")
        print("[stt] Model ready.", flush=True)
    return _model


def transcribe_once() -> str:
    """
    Wait for speech, record until silence, and return the transcribed text.
    Returns an empty string if nothing was captured.
    """
    audio = _record_utterance()
    if audio is None or len(audio) == 0:
        return ""
    return _transcribe(audio)


def _record_utterance() -> np.ndarray | None:
    """
    Record audio using energy-based VAD.
    Waits for speech onset, then records until silence.
    """
    threshold = config.AUDIO_ENERGY_THRESHOLD
    device = config.MIC_DEVICE

    audio_q: queue.Queue[np.ndarray] = queue.Queue()

    def _callback(indata, frames, time, status):
        audio_q.put(indata[:, 0].copy())

    chunks: list[np.ndarray] = []
    silent_count = 0
    has_speech = False

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=CHUNK_SAMPLES,
        device=device,
        dtype="int16",
        channels=1,
        callback=_callback,
    ):
        print("[stt] Listening...", flush=True)
        for _ in range(MAX_CHUNKS):
            chunk = audio_q.get()
            rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))

            if rms > threshold:
                has_speech = True
                silent_count = 0
                chunks.append(chunk)
            elif has_speech:
                chunks.append(chunk)
                silent_count += 1
                if silent_count >= SILENCE_CHUNKS:
                    break

    if not chunks:
        return None
    return np.concatenate(chunks)


def _transcribe(audio: np.ndarray) -> str:
    """Transcribe a numpy int16 audio array. Returns stripped text."""
    model = _get_model()
    # faster-whisper expects float32 normalised to [-1, 1]
    audio_f32 = audio.astype(np.float32) / 32768.0
    segments, _ = model.transcribe(
        audio_f32,
        language="en",
        beam_size=1,          # fastest setting
        vad_filter=True,      # built-in VAD to skip silence
    )
    return " ".join(s.text.strip() for s in segments).strip()

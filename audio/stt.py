"""
Speech-to-text:
  - Wake word detection  → local faster-whisper (always-on, runs in a loop)
  - Command transcription → OpenAI Whisper API  (one call per command)

Recording uses energy-based VAD: starts on speech onset, stops on silence.

Requirements:
  pip install faster-whisper sounddevice openai
"""

import io
import queue
import wave

import numpy as np
import sounddevice as sd

import config

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1600       # 100 ms per chunk
SILENCE_CHUNKS = 15        # 1.5 s of silence → end of utterance
MAX_CHUNKS = 100           # 10 s hard cap

# Shared local model instance — used by wake_word.py, loaded once
_model = None


def _get_model():
    """Return the local faster-whisper model (for wake word detection)."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        name = config.WHISPER_MODEL
        print(f"[stt] Loading local Whisper model '{name}'...", flush=True)
        _model = WhisperModel(name, device="cpu", compute_type="int8")
        print("[stt] Model ready.", flush=True)
    return _model


def _transcribe(audio: np.ndarray) -> str:
    """Transcribe a numpy int16 array locally (used by wake_word.py)."""
    model = _get_model()
    audio_f32 = audio.astype(np.float32) / 32768.0
    segments, _ = model.transcribe(
        audio_f32,
        language="en",
        beam_size=1,
        vad_filter=True,
    )
    return " ".join(s.text.strip() for s in segments).strip()


def transcribe_once() -> str:
    """
    Record one spoken command and transcribe it via the OpenAI Whisper API.
    Returns an empty string if nothing was captured.
    """
    audio = _record_utterance()
    if audio is None or len(audio) == 0:
        return ""
    return _transcribe_api(audio)


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


def _transcribe_api(audio: np.ndarray) -> str:
    """Send audio to the OpenAI Whisper API and return the transcript."""
    import openai

    client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

    # Build an in-memory WAV file — OpenAI API requires a named file-like object
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)          # int16 = 2 bytes per sample
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    buf.name = "audio.wav"

    print("[stt] Transcribing via OpenAI Whisper API...", flush=True)
    result = client.audio.transcriptions.create(
        model=config.STT_MODEL,
        file=buf,
        language="en",
    )
    return result.text.strip()

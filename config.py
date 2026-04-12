import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
PRIMARY_MODEL = "qwen/qwen-2.5-72b-instruct"
FALLBACK_MODEL = "google/gemini-flash-1.5"

# --- Audio ---
# None = use system default mic.
# On Pi, set to the substring of the HFP device name shown by: python -m sounddevice
# e.g. MIC_DEVICE = "bluez"  or the integer device index
MIC_DEVICE = None

# faster-whisper model size. Downloaded automatically from HuggingFace on first use.
# Options (English-only variants are faster): tiny.en, base.en, small.en, medium.en
# Recommended: "base.en" (~145 MB) — good balance of speed and accuracy on Pi 5
WHISPER_MODEL = "base.en"

# Wake word keyword — matched as a whole word in the transcription.
# With Whisper you can use the actual word "pi" directly.
WAKE_WORD_KEYWORD = "hello"

# RMS energy threshold for speech onset detection (0–32768).
# Increase if the mic picks up too much background noise.
AUDIO_ENERGY_THRESHOLD = 300

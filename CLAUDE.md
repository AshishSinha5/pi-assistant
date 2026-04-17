# Pi Assistant — Project Context for Claude Code

## What this is
A voice-activated LLM agent running on a Raspberry Pi 5. You say a wake word ("Pi"), speak a command, and the agent executes it via tool calls. First tool: play music from YouTube.

---

## Hardware

| Component | Details |
|---|---|
| Board | Raspberry Pi 5, 8GB RAM |
| Mic | USB microphone (always available, no profile switching needed) |
| Speaker | Sony WH-1000XM5 (Bluetooth A2DP, stays in A2DP permanently) |
| Storage | (SD card / NVMe — update as needed) |
| Network | WiFi (needed for OpenRouter API + YouTube streaming) |

---

## Pi OS & Environment

| | |
|---|---|
| OS | Ubuntu 24.04 LTS (headless, no desktop) |
| Hostname | `ashish-pi` |
| Local IP | `192.168.29.x` (home network) |
| Access | SSH from MacBook |
| Audio daemon | PipeWire (default on Ubuntu 24.04) |
| Python | 3.12 (system default on Ubuntu 24.04) |

---

## Dev Machine

| | |
|---|---|
| Machine | MacBook (Apple Silicon) |
| Purpose | Development, testing LLM agent logic locally |
| Python | Use virtualenv, match 3.12 where possible |

---

## Audio Architecture

Two separate audio devices:

- **USB mic** — always on, used for wake word detection and STT
- **Sony XM5 (Bluetooth)** — A2DP only, used for music/audio playback

No profile switching needed. XM5 stays in `a2dp_sink` permanently.
`audio/bluetooth.py` is retained but not called from the main loop.

---

## Project Structure

```
pi-assistant/
├── CLAUDE.md                  # this file
├── config.py                  # env vars, OpenRouter settings, device config
├── main.py                    # orchestrator — voice mode (Pi) or test mode (Mac)
│
├── agent/
│   ├── agent.py               # LLM loop + tool dispatch
│   └── tool_registry.py       # tool registration pattern
│
├── tools/
│   ├── __init__.py
│   ├── music.py               # yt-dlp + mpv player (real streaming on Mac + Pi)
│   └── light.py               # turn_on_light + turn_off_light via python-kasa (Tapo)
│
├── audio/
│   ├── wake_word.py           # openWakeWord listener (Pi only)
│   ├── stt.py                 # Vosk STT (Pi only)
│   └── bluetooth.py           # HFP ↔ A2DP profile switching (Pi only)
│
├── tests/
│   └── test_agent_mac.py      # interactive text-input loop for Mac testing
│
└── requirements.txt
```

---

## Run Modes

```bash
# Mac — text input, real yt-dlp + mpv music streaming, no audio pipeline deps
python main.py --mode test

# Pi — full voice pipeline
python main.py --mode voice
```

`--mode test` skips all audio pipeline imports (wake word, STT, Bluetooth). Safe to run on Mac.
Music streaming via yt-dlp + mpv works in both modes.

---

## LLM / API

| | |
|---|---|
| Provider | OpenRouter (`https://openrouter.ai/api/v1`) |
| API format | OpenAI-compatible |
| Primary model | `qwen/qwen-2.5-72b-instruct` (free, strong tool calling) |
| Fallback model | `google/gemini-flash-1.5` |
| Auth | `OPENROUTER_API_KEY` in `.env` |

---

## Tool Registry Pattern

Adding a new tool = one schema dict + one function + one register call. The LLM automatically sees all registered tools on every call.

```python
# tools/weather.py
def get_weather(city: str) -> str:
    ...

TOOL_SCHEMA = {
    "name": "get_weather",
    "description": "Get current weather for a city",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"}
        },
        "required": ["city"]
    }
}

# In tool_registry.py — one line to add:
from tools.weather import get_weather, TOOL_SCHEMA
register(TOOL_SCHEMA, get_weather)
```

---

## Phase Plan

### Phase 1 — Mac (LLM + tools + mic pipeline) ✅ complete
- `agent.py` + `tool_registry.py`
- `tools/music.py` — real yt-dlp + mpv streaming (Mac + Pi)
- `tools/music.py` — `stop_music` tool
- `audio/stt.py` — Vosk STT, silence-detection, works on Mac mic + Pi HFP mic
- `audio/wake_word.py` — openWakeWord listener, works on Mac + Pi
- `audio/bluetooth.py` — HFP↔A2DP switching (Pi only, skipped on Mac)
- `tests/test_agent_mac.py` — interactive text-input loop
- Two run modes: `--mode test` (text), `--mode voice` (mic pipeline, Mac + Pi)
- Mac prereqs: `brew install mpv` + `pip install -r requirements.txt`
- Vosk model: download `vosk-model-small-en-us-0.15` → `models/` directory
- Wake word: `hey_jarvis` (bundled). Train a custom "pi" model before Phase 3.

### Phase 2 — Pi audio pipeline
- `audio/stt.py` — Vosk transcription
- `audio/wake_word.py` — openWakeWord ("Pi" keyword)
- `audio/bluetooth.py` — profile switching logic

### Phase 3 — Integration
- `main.py` ties voice pipeline + agent
- End-to-end: say "Pi" → speak command → music plays

### Phase 4 — New tools (in progress)
- `tools/light.py` — `turn_on_light` / `turn_off_light` via python-kasa (Tapo) ✅ complete
- Timer / alarm
- Weather
- News briefing

---

## Key Decisions & Rationale

| Decision | Rationale |
|---|---|
| XM5 HFP↔A2DP switching | Single device simplicity; switch profile per task |
| OpenRouter + Qwen free tier | No infra cost, reliable tool calling, easy to swap models |
| Vosk for STT | Already proven on this Pi in a prior speaker verification project |
| openWakeWord | Fully open source, runs on Pi without cloud |
| yt-dlp + mpv | No YouTube API key needed, streams audio-only cleanly |
| Two run modes | Develop/test on Mac, deploy on Pi — no audio dep issues |

---

## Prior Pi Projects on this device
- Speaker verification system using Vosk + SpeechBrain ECAPA-TDNN
- GPIO control via NPN transistor triggered by speaker identity
- Boot-on-startup via crontab

Vosk is already installed and tested on this Pi.

---

## Notes
- Always check if a command is Pi-only before running on Mac (audio, GPIO, Bluetooth)
- `.env` file holds `OPENROUTER_API_KEY`, `KASA_USERNAME`, `KASA_PASSWORD`, `TAPO_HOST` — never commit this
- `bluez_card` ID for XM5 needs to be detected dynamically, not hardcoded
- Tapo light control uses python-kasa with async API (wrapped in `asyncio.run` for sync compatibility); `TAPO_HOST` must be the local IP of the device
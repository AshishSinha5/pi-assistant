# Pi Assistant — Project Context for Claude Code

## What this is
A voice-activated LLM agent running on a Raspberry Pi 5. Say a wake word, speak a command, and the agent executes it via tool calls.

---

## Hardware

| Component | Details |
|---|---|
| Board | Raspberry Pi 5, 8GB RAM |
| Mic | USB microphone (always available) |
| Speaker | Sony WH-1000XM5 (Bluetooth A2DP, stays in A2DP permanently) |
| Storage | (SD card / NVMe — update as needed) |
| Network | WiFi (needed for OpenRouter API + OpenAI API + YouTube streaming) |

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

Two separate audio devices — no profile switching needed:

- **USB mic** — always on, used for wake word detection and STT recording
- **Sony XM5 (Bluetooth)** — A2DP only, used for music/audio playback. Stays in `a2dp_sink` permanently.

`audio/bluetooth.py` is retained for manual profile switching but is not called from the main loop.

---

## STT Architecture

Two-stage transcription:

| Stage | Method | Rationale |
|---|---|---|
| Wake word | Local faster-whisper (`WHISPER_MODEL`) | Always-on, free, no network latency |
| Command STT | OpenAI Whisper API (`STT_MODEL`) | Higher accuracy, one call per command |

`STT_MODEL` options: `whisper-1`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe`

---

## Project Structure

```
pi-assistant/
├── CLAUDE.md                  # this file
├── config.py                  # env vars, model settings, audio config
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
│   ├── wake_word.py           # faster-whisper wake word (local inference, 3-second windows)
│   ├── stt.py                 # energy-based VAD recorder + OpenAI Whisper API transcription
│   └── bluetooth.py           # A2DP/HFP helpers (retained, not used in main loop)
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

`--mode test` skips all audio pipeline imports. Safe to run on Mac.

---

## LLM / API

| | |
|---|---|
| Provider | OpenRouter (`https://openrouter.ai/api/v1`) |
| API format | OpenAI-compatible |
| Primary model | `qwen/qwen-2.5-72b-instruct` (free, strong tool calling) |
| Fallback model | `google/gemini-flash-1.5` |
| Auth | `OPENROUTER_API_KEY` in `.env` |
| STT | OpenAI Whisper API (`OPENAI_API_KEY` in `.env`) |

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

# In main.py _register_tools():
from tools.weather import get_weather, TOOL_SCHEMA as WEATHER_SCHEMA
tool_registry.register(WEATHER_SCHEMA, get_weather)
```

---

## Phase Plan

### Phase 1 — Mac (LLM + tools + mic pipeline) ✅ complete
- `agent.py` + `tool_registry.py`
- `tools/music.py` — real yt-dlp + mpv streaming (Mac + Pi)
- `tools/music.py` — `stop_music` tool
- `tests/test_agent_mac.py` — interactive text-input loop
- Two run modes: `--mode test` (text), `--mode voice` (mic pipeline)

### Phase 2 — Pi audio pipeline ✅ complete
- `audio/stt.py` — energy-based VAD recorder + OpenAI Whisper API transcription
- `audio/wake_word.py` — local faster-whisper wake word detection
- USB mic as audio input; XM5 in A2DP for output (no profile switching)

### Phase 3 — Integration ✅ complete
- `main.py` ties voice pipeline + agent
- End-to-end: say wake word → speak command → tool executes
- Systemd service for boot-on-startup

### Phase 4 — New tools (in progress)
- `tools/light.py` — `turn_on_light` / `turn_off_light` via python-kasa (Tapo) ✅ complete
- Timer / alarm
- Weather
- News briefing

---

## Key Decisions & Rationale

| Decision | Rationale |
|---|---|
| USB mic + XM5 A2DP (no HFP) | XM5 HFP showed `available: no` on PipeWire without ofono; USB mic is simpler and always works |
| faster-whisper for wake word | Local inference — always-on loop, no API cost or latency |
| OpenAI Whisper API for STT | Better accuracy than local model; one call per command keeps cost negligible |
| OpenRouter + Qwen free tier | No infra cost, reliable tool calling, easy to swap models |
| yt-dlp + mpv | No YouTube API key needed, streams audio-only cleanly |
| python-kasa for Tapo | Official async library; wrapped in `asyncio.run` for sync tool registry |
| Systemd service | Reliable boot-on-startup, easy log access via journalctl |

---

## Prior Pi Projects on this device
- Speaker verification system using Vosk + SpeechBrain ECAPA-TDNN
- GPIO control via NPN transistor triggered by speaker identity
- Boot-on-startup via crontab

---

## Notes
- Always check if a command is Pi-only before running on Mac (audio, GPIO, Bluetooth)
- `.env` holds `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `KASA_USERNAME`, `KASA_PASSWORD`, `TAPO_HOST` — never commit this
- `TAPO_HOST` must be the local IP of the Tapo device (find it in the Tapo app)
- Tapo light control uses python-kasa async API wrapped in `asyncio.run` for sync compatibility
- XM5 bluez card ID is `bluez_card.F8_5C_7E_45_98_8E` — available profiles: `a2dp_sink` (yes), `handsfree_head_unit` (no, requires ofono)

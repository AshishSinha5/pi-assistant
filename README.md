# Pi Assistant

A voice-activated LLM agent running on a Raspberry Pi 5. Say a wake word, speak a command, and the agent executes it via tool calls — starting with playing music from YouTube.

---

## Hardware

| Component | Details |
|---|---|
| Board | Raspberry Pi 5, 8GB RAM |
| Audio | Sony WH-1000XM5 (Bluetooth — mic via HFP, playback via A2DP) |
| OS | Ubuntu 24.04 LTS (headless) |

---

## How it works

```
Wake word heard → STT transcribes command → LLM decides tool → Tool executes
```

- **Wake word** — faster-whisper listens in 3-second windows and fires when the configured keyword is heard
- **STT** — faster-whisper records until silence and returns the transcribed command
- **LLM** — OpenRouter (Qwen 2.5 72B) receives the command and calls tools
- **Tools** — `play_music` streams audio via yt-dlp + mpv; `stop_music` kills playback; `turn_on_light` / `turn_off_light` control a Tapo smart light via python-kasa

---

## Project structure

```
pi-assistant/
├── config.py                  # All settings (model, wake word, mic, thresholds)
├── main.py                    # Entry point — --mode test or --mode voice
│
├── agent/
│   ├── agent.py               # LLM loop + tool dispatch
│   └── tool_registry.py       # Register tools with one line each
│
├── tools/
│   ├── music.py               # play_music + stop_music (yt-dlp + mpv)
│   └── light.py               # turn_on_light + turn_off_light (python-kasa / Tapo)
│
├── audio/
│   ├── stt.py                 # faster-whisper STT with energy-based VAD
│   ├── wake_word.py           # faster-whisper wake word detection
│   └── bluetooth.py           # HFP ↔ A2DP profile switching (Pi only)
│
└── tests/
    └── test_agent_mac.py      # Interactive text-input loop for Mac testing
```

---

## Setup

### Prerequisites

**Mac:**
```bash
brew install mpv
```

**Pi:**
```bash
sudo apt install mpv
```

### Install Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure API key and smart home

```bash
cp .env.example .env
# Edit .env and fill in your keys
```

```
OPENROUTER_API_KEY=your_key_here   # free at openrouter.ai
KASA_USERNAME=your@email.com       # Tapo/Kasa account
KASA_PASSWORD=yourpassword
TAPO_HOST=192.168.x.x              # local IP of the Tapo device
```

---

## Running

### Text mode (Mac — no mic needed)

```bash
python main.py --mode test
```

Type commands at the prompt. Real music streams via mpv. Type `reset` to clear conversation history, `quit` to exit.

### Voice mode (Mac or Pi)

```bash
python main.py --mode voice
```

1. The Whisper model downloads automatically on first run (~145 MB)
2. Say the wake word (default: `"hey there"`) — configured in `config.py`
3. Speak your command after "Listening for your command..."
4. The agent runs and music plays

On Pi, Bluetooth profile switches automatically (HFP for mic → A2DP for playback).

---

## Configuration

All settings live in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `WHISPER_MODEL` | `"base.en"` | Model size: `tiny.en`, `base.en`, `small.en`, `medium.en` |
| `WAKE_WORD_KEYWORD` | `"hey there"` | Phrase to trigger the assistant |
| `AUDIO_ENERGY_THRESHOLD` | `3000` | Mic sensitivity for command recording (0–32768) |
| `MIC_DEVICE` | `None` | Mic device name/index (`None` = system default) |
| `PRIMARY_MODEL` | `qwen/qwen-2.5-72b-instruct` | LLM via OpenRouter |

---

## Adding a new tool

One schema dict + one function + one register call:

```python
# tools/weather.py
def get_weather(city: str) -> str:
    return f"Weather in {city}: sunny"

TOOL_SCHEMA = {
    "name": "get_weather",
    "description": "Get current weather for a city",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
    }
}
```

Then in `main.py` inside `_register_tools()`:
```python
from tools.weather import get_weather, TOOL_SCHEMA as WEATHER_SCHEMA
tool_registry.register(WEATHER_SCHEMA, get_weather)
```

---

## Phase plan

| Phase | Status | Description |
|---|---|---|
| 1 | ✅ Complete | LLM + tools + real music streaming + mic pipeline on Mac |
| 2 | Planned | Pi audio pipeline (Bluetooth profile switching wired up) |
| 3 | Planned | Full integration — wake word → speech → music plays on Pi |
| 4 | In progress | New tools: timers, weather, news |

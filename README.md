# Pi Assistant

A voice-activated LLM agent running on a Raspberry Pi 5. Say a wake word, speak a command, and the agent executes it via tool calls.

---

## Hardware

| Component | Details |
|---|---|
| Board | Raspberry Pi 5, 8GB RAM |
| Mic | USB microphone |
| Speaker | Sony WH-1000XM5 (Bluetooth A2DP) |
| OS | Ubuntu 24.04 LTS (headless) |

---

## How it works

```
Wake word heard → STT transcribes command → LLM decides tool → Tool executes
```

- **Wake word** — faster-whisper listens locally in 3-second windows and fires when the configured keyword is heard
- **STT** — OpenAI Whisper API transcribes the spoken command (model configurable via `STT_MODEL`)
- **LLM** — OpenRouter (Qwen 2.5 72B) receives the command and calls tools
- **Tools** — `play_music` streams audio via yt-dlp + mpv; `stop_music` kills playback; `turn_on_light` / `turn_off_light` control a Tapo smart light via python-kasa

---

## Project structure

```
pi-assistant/
├── config.py                  # All settings (models, wake word, mic, thresholds)
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
│   ├── stt.py                 # Energy-based VAD recorder + OpenAI Whisper API transcription
│   ├── wake_word.py           # faster-whisper wake word detection (local, always-on)
│   └── bluetooth.py           # A2DP helpers (retained, not called from main loop)
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

### Configure keys

Copy `.env.example` to `.env` and fill in:

```
OPENROUTER_API_KEY=your_key_here   # free at openrouter.ai — used for LLM
OPENAI_API_KEY=sk-...              # openai.com — used for Whisper STT
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

1. Say the wake word (default: `"hello"`) — configured in `config.py`
2. Speak your command after the listening tone
3. The agent runs the appropriate tool

---

## Configuration

All settings live in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `WAKE_WORD_KEYWORD` | `"hello"` | Phrase to trigger the assistant |
| `WHISPER_MODEL` | `"base"` | Local faster-whisper model for wake word (tiny / base / small) |
| `STT_MODEL` | `"gpt-4o-mini-transcribe"` | OpenAI model for command STT (`whisper-1`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe`) |
| `AUDIO_ENERGY_THRESHOLD` | `200` | Mic sensitivity for VAD (0–32768) |
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

## Run as a service (Pi)

```bash
sudo systemctl enable --now pi-assistant
journalctl -u pi-assistant -f   # live logs
```

See `pi-assistant.service` for the systemd unit file.

---

## Phase plan

| Phase | Status | Description |
|---|---|---|
| 1 | ✅ Complete | LLM + tools + real music streaming + mic pipeline |
| 2 | ✅ Complete | Pi audio pipeline — USB mic, faster-whisper wake word, OpenAI STT |
| 3 | ✅ Complete | Full integration — wake word → speech → tool executes on Pi |
| 4 | In progress | New tools: timers, weather, news |

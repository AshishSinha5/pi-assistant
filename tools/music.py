"""
Music tool — searches YouTube via yt-dlp and streams audio via mpv.

Works on both Mac and Pi. Requires:
  Mac:  brew install mpv  &&  pip install yt-dlp
  Pi:   sudo apt install mpv  &&  pip install yt-dlp
"""

import subprocess
import sys
import openai
import config

TOOL_SCHEMA = {
    "name": "play_music",
    "description": (
        "Search YouTube and play a song or audio. "
        "Use this whenever the user asks to play music, a song, or an artist."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query, e.g. 'Bohemian Rhapsody Queen' or 'lo-fi chill beats'",
            }
        },
        "required": ["query"],
    },
}

_IS_MAC = sys.platform == "darwin"
_mpv_process: subprocess.Popen | None = None


STOP_SCHEMA = {
    "name": "stop_music",
    "description": "Stop the currently playing music.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}


def _refine_query(raw: str) -> str:
    """
    Pass the raw STT query through the LLM to fix transcription errors
    and produce a clean YouTube search string.
    """
    client = openai.OpenAI(
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,
    )
    response = client.chat.completions.create(
        model=config.PRIMARY_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a music search assistant. "
                    "The user asked to play music but the request was captured by speech-to-text "
                    "and may contain transcription errors. "
                    "Return ONLY a clean YouTube search query (artist + song/genre)."
                    "Query may be distorted by transcription error re write based on phinetic similarity, "
                    "No explanation, no punctuation, just the search string."
                ),
            },
            {"role": "user", "content": raw},
        ],
        max_tokens=40,
        temperature=0,
    )
    refined = response.choices[0].message.content.strip().strip('"').strip("'")
    if refined and refined != raw:
        print(f"[music] Query refined: {raw!r} → {refined!r}")
    return refined or raw


def play_music(query: str) -> str:
    """Search YouTube for `query` and stream audio via mpv."""
    global _mpv_process

    # Stop any existing playback before starting new
    _stop()

    # query = _refine_query(query)
    print(f"[music] Searching YouTube for: {query!r}")

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--no-playlist",
                "--get-url",
                "--format", "bestaudio",
                f"ytsearch1:{query}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "Error: yt-dlp timed out while searching YouTube."
    except FileNotFoundError:
        return "Error: yt-dlp not found. Run: pip install yt-dlp"

    stream_url = result.stdout.strip()
    if not stream_url:
        return f"Could not find a YouTube result for: {query}"

    print(f"[music] Streaming via mpv...")

    try:
        _mpv_process = subprocess.Popen(
            ["mpv", "--no-video", "--really-quiet", stream_url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        install_hint = "brew install mpv" if _IS_MAC else "sudo apt install mpv"
        return f"Error: mpv not found. Run: {install_hint}"

    return f"Now playing: {query}"


def stop_music() -> str:
    """Stop the currently playing music."""
    stopped = _stop()
    return "Music stopped." if stopped else "Nothing is playing."


def _stop() -> bool:
    """Kill the mpv process if running. Returns True if something was stopped."""
    global _mpv_process
    if _mpv_process is not None and _mpv_process.poll() is None:
        _mpv_process.terminate()
        _mpv_process = None
        return True
    _mpv_process = None
    return False

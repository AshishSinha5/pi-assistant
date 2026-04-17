"""
Entry point for Pi Assistant.

  --mode test   Text-input mode — LLM + tools + real music, no mic (Mac-safe)
  --mode voice  Voice pipeline — wake word → STT → agent (Mac + Pi)
               On Pi: also does HFP↔A2DP Bluetooth switching.
"""

import argparse


def _register_tools():
    from agent import tool_registry
    from tools.music import play_music, stop_music, TOOL_SCHEMA as MUSIC_SCHEMA, STOP_SCHEMA
    from tools.light import turn_on_light, turn_off_light, TURN_ON_SCHEMA, TURN_OFF_SCHEMA
    tool_registry.register(MUSIC_SCHEMA, play_music)
    tool_registry.register(STOP_SCHEMA, stop_music)
    tool_registry.register(TURN_ON_SCHEMA, turn_on_light)
    tool_registry.register(TURN_OFF_SCHEMA, turn_off_light)


def main():
    parser = argparse.ArgumentParser(description="Pi Assistant")
    parser.add_argument(
        "--mode",
        choices=["test", "voice"],
        default="test",
        help="'test' for text input, 'voice' for mic pipeline",
    )
    args = parser.parse_args()

    if args.mode == "test":
        _run_test_mode()
    elif args.mode == "voice":
        _run_voice_mode()


def _run_test_mode():
    _register_tools()
    from tests.test_agent_mac import run_interactive_loop
    run_interactive_loop()


def _run_voice_mode():
    _register_tools()

    from agent import agent
    from audio.wake_word import wait_for_wake_word
    from audio.stt import transcribe_once
    from audio.tones import play_listening_tone, play_done_tone

    history = []

    print("Pi Assistant — voice mode")
    print("Say the wake word to start.\n")

    while True:
        wait_for_wake_word()
        play_listening_tone()
        print("Listening for your command...", flush=True)

        text = transcribe_once()
        if not text:
            play_done_tone()
            print("[voice] Nothing heard, going back to sleep.\n")
            continue

        print(f"You: {text}")

        response, history = agent.run(text, history)
        print(f"Pi: {response}\n")
        play_done_tone()
        # Future Phase 3: TTS speaks `response` here


if __name__ == "__main__":
    main()

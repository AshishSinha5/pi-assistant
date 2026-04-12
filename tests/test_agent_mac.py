"""
Interactive text-input loop for testing the LLM agent + tools on Mac.
No audio dependencies — safe to run anywhere.

Usage:
    python main.py --mode test
    # or directly:
    python -m tests.test_agent_mac
"""

from agent import agent


def run_interactive_loop():
    print("Pi Assistant — test mode (text input)")
    print("Type your command, or 'quit' / 'exit' to stop.")
    print("Type 'reset' to start a fresh conversation.\n")

    history = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye.")
            break
        if user_input.lower() == "reset":
            history = []
            print("[conversation reset]\n")
            continue

        response, history = agent.run(user_input, history)
        print(f"Pi: {response}\n")


if __name__ == "__main__":
    # Allow running standalone: python -m tests.test_agent_mac
    # Need to set up tools first when running directly
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from agent import tool_registry
    from tools.music import play_music, stop_music, TOOL_SCHEMA as MUSIC_SCHEMA, STOP_SCHEMA
    tool_registry.register(MUSIC_SCHEMA, play_music)
    tool_registry.register(STOP_SCHEMA, stop_music)

    run_interactive_loop()

"""
LLM agent loop with tool calling via OpenRouter.
Handles multi-turn conversation and automatic tool dispatch.
"""

import json
import openai
import config
from agent import tool_registry

SYSTEM_PROMPT = """You are Pi, a helpful voice assistant running on a Raspberry Pi.
You have access to tools that let you control media, answer questions, and more.
Keep responses concise — they will be spoken aloud.
When the user asks to play music, always use the play_music tool."""


def run(user_message: str, history: list[dict] | None = None) -> tuple[str, list[dict]]:
    """
    Run one turn of the agent loop.

    Args:
        user_message: The latest user input.
        history: Prior conversation turns (mutated in place and returned).

    Returns:
        (assistant_text, updated_history)
    """
    if history is None:
        history = []

    client = openai.OpenAI(
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,
    )

    history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    tools = tool_registry.get_schemas()

    # Agentic loop — keep calling LLM until it stops requesting tool calls
    while True:
        response = client.chat.completions.create(
            model=config.PRIMARY_MODEL,
            messages=messages,
            tools=tools if tools else openai.NOT_GIVEN,
            tool_choice="auto" if tools else openai.NOT_GIVEN,
        )

        message = response.choices[0].message

        # Append raw assistant message to conversation
        messages.append(message)
        history.append({"role": "assistant", "content": message.content, "tool_calls": getattr(message, "tool_calls", None)})

        # No tool calls → we have the final text response
        if not message.tool_calls:
            return message.content or "", history

        # Execute each tool call and feed results back
        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}

            print(f"[tool] {fn_name}({arguments})")
            result = tool_registry.dispatch(fn_name, arguments)
            print(f"[tool result] {result}")

            tool_result_msg = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
            messages.append(tool_result_msg)
            history.append(tool_result_msg)

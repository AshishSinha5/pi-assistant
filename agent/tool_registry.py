"""
Central tool registry. Each tool registers a JSON schema (for the LLM)
and a callable (for dispatch). The agent reads both at runtime.
"""

_tools: dict[str, dict] = {}   # name -> {"schema": ..., "fn": ...}


def register(schema: dict, fn) -> None:
    """Register a tool. `schema` must follow the OpenAI function-calling format."""
    name = schema["name"]
    _tools[name] = {"schema": schema, "fn": fn}


def get_schemas() -> list[dict]:
    """Return all tool schemas in the format the LLM expects."""
    return [
        {"type": "function", "function": t["schema"]}
        for t in _tools.values()
    ]


def dispatch(name: str, arguments: dict) -> str:
    """Call the function registered under `name` with `arguments`."""
    if name not in _tools:
        return f"Error: unknown tool '{name}'"
    try:
        result = _tools[name]["fn"](**arguments)
        return str(result)
    except Exception as e:
        return f"Error executing tool '{name}': {e}"

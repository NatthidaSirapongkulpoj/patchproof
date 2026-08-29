from __future__ import annotations

import json
from typing import Any


ALLOWED_ACTIONS = {
    "list_files",
    "read_file",
    "search_text",
    "write_file",
    "run_command",
    "finish",
}


class InvalidAgentAction(ValueError):
    pass


def parse_agent_action(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidAgentAction(
            f"Agent output is not valid JSON: {exc}"
        ) from exc

    if not isinstance(value, dict):
        raise InvalidAgentAction(
            "Agent action must be a JSON object"
        )

    action = value.get("action")

    if action not in ALLOWED_ACTIONS:
        raise InvalidAgentAction(
            f"Unsupported action: {action}"
        )

    return value

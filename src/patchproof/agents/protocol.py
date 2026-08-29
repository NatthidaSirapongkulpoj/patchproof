from __future__ import annotations

import json
from typing import Any


ALLOWED_ACTIONS = {
    "list_files",
    "read_file",
    "search_text",
    "write_file",
    "replace_text",
    "run_command",
    "finish",
}


class InvalidAgentAction(ValueError):
    pass


def _require_string(
    value: dict[str, Any],
    field: str,
) -> None:
    if field not in value:
        raise InvalidAgentAction(
            f"Missing required field: {field}"
        )

    if not isinstance(value[field], str):
        raise InvalidAgentAction(
            f"Field '{field}' must be a string"
        )


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

    if action == "list_files":
        if "path" in value and not isinstance(
            value["path"],
            str,
        ):
            raise InvalidAgentAction(
                "Field 'path' must be a string"
            )

    elif action == "read_file":
        _require_string(value, "path")

    elif action == "search_text":
        _require_string(value, "query")

    elif action == "write_file":
        _require_string(value, "path")
        _require_string(value, "content")

    elif action == "replace_text":
        _require_string(value, "path")
        _require_string(value, "old")
        _require_string(value, "new")

        if value["old"] == "":
            raise InvalidAgentAction(
                "Field 'old' must not be empty"
            )

    elif action == "run_command":
        _require_string(value, "command")

    elif action == "finish":
        _require_string(value, "summary")

    return value

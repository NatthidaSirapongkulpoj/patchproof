import pytest

from patchproof.agents.protocol import (
    InvalidAgentAction,
    parse_agent_action,
)


def test_parse_valid_read_file_action() -> None:
    action = parse_agent_action(
        '{"action":"read_file","path":"app/main.py"}'
    )

    assert action == {
        "action": "read_file",
        "path": "app/main.py",
    }


def test_rejects_invalid_json() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="not valid JSON",
    ):
        parse_agent_action(
            '{"action":"read_file","path":"app/main.py"'
        )


def test_rejects_unsupported_action() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="Unsupported action",
    ):
        parse_agent_action(
            '{"action":"delete_file","path":"app/main.py"}'
        )


def test_replace_text_action_is_allowed() -> None:
    action = parse_agent_action(
        (
            '{"action":"replace_text",'
            '"path":"app/main.py",'
            '"old":"quantity: int",'
            '"new":"quantity: int = Field(ge=1)"}'
        )
    )

    assert action["action"] == "replace_text"
    assert action["path"] == "app/main.py"
    assert action["old"] == "quantity: int"
    assert action["new"] == "quantity: int = Field(ge=1)"


def test_replace_text_requires_path() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="Missing required field: path",
    ):
        parse_agent_action(
            (
                '{"action":"replace_text",'
                '"old":"before",'
                '"new":"after"}'
            )
        )


def test_replace_text_requires_old() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="Missing required field: old",
    ):
        parse_agent_action(
            (
                '{"action":"replace_text",'
                '"path":"app/main.py",'
                '"new":"after"}'
            )
        )


def test_replace_text_requires_new() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="Missing required field: new",
    ):
        parse_agent_action(
            (
                '{"action":"replace_text",'
                '"path":"app/main.py",'
                '"old":"before"}'
            )
        )


def test_replace_text_rejects_empty_old() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="must not be empty",
    ):
        parse_agent_action(
            (
                '{"action":"replace_text",'
                '"path":"app/main.py",'
                '"old":"",'
                '"new":"after"}'
            )
        )


def test_write_file_requires_content() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="Missing required field: content",
    ):
        parse_agent_action(
            '{"action":"write_file","path":"app/main.py"}'
        )


def test_run_command_requires_command() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="Missing required field: command",
    ):
        parse_agent_action(
            '{"action":"run_command"}'
        )


def test_finish_requires_summary() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="Missing required field: summary",
    ):
        parse_agent_action(
            '{"action":"finish"}'
        )


def test_action_must_be_json_object() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="must be a JSON object",
    ):
        parse_agent_action(
            '["read_file", "app/main.py"]'
        )


def test_string_fields_must_be_strings() -> None:
    with pytest.raises(
        InvalidAgentAction,
        match="Field 'path' must be a string",
    ):
        parse_agent_action(
            '{"action":"read_file","path":123}'
        )

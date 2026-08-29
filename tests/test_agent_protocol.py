import pytest

from patchproof.agents.protocol import (
    InvalidAgentAction,
    parse_agent_action,
)


def test_parse_valid_read_action() -> None:
    result = parse_agent_action(
        '{"action":"read_file","path":"app/main.py"}'
    )

    assert result["action"] == "read_file"
    assert result["path"] == "app/main.py"


def test_reject_non_json() -> None:
    with pytest.raises(InvalidAgentAction):
        parse_agent_action(
            "I think you should edit app/main.py"
        )


def test_reject_unknown_action() -> None:
    with pytest.raises(InvalidAgentAction):
        parse_agent_action(
            '{"action":"delete_everything"}'
        )

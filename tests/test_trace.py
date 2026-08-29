import json
from pathlib import Path

from patchproof.trace import TraceRecorder


def test_trace_recorder_writes_jsonl(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "trace.jsonl"

    recorder = TraceRecorder(
        trace_path=trace_path,
        run_id="run-001",
        agent_name="baseline-agent",
    )

    recorder.record(
        "instruction",
        {
            "issue": "example",
        },
    )

    recorder.record(
        "tool_call",
        {
            "path": "app/main.py",
        },
        tool_name="read_file",
    )

    lines = trace_path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["step"] == 1
    assert first["event_type"] == "instruction"

    assert second["step"] == 2
    assert second["tool_name"] == "read_file"

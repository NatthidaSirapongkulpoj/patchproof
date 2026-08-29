from pathlib import Path

from patchproof.agents.baseline import BaselineAgent
from patchproof.agents.provider import (
    ModelProvider,
    ModelResponse,
)
from patchproof.trace import TraceRecorder


class FakeProvider(ModelProvider):
    def __init__(self) -> None:
        self.responses = iter(
            [
                '{"action":"read_file","path":"app/main.py"}',
                '{"action":"finish","summary":"done"}',
            ]
        )

    def generate(
        self,
        messages: list[dict[str, str]],
    ) -> ModelResponse:
        return ModelResponse(
            text=next(self.responses),
            model="fake-model",
        )


def test_baseline_agent_loop(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"

    (repo / "app").mkdir(
        parents=True
    )

    (repo / "app" / "main.py").write_text(
        "x = 1\n",
        encoding="utf-8",
    )

    trace = TraceRecorder(
        trace_path=tmp_path / "trace.jsonl",
        run_id="test-run",
        agent_name="baseline-agent",
    )

    agent = BaselineAgent(
        provider=FakeProvider(),
        system_prompt="test prompt",
        max_actions=4,
    )

    result = agent.run(
        repository_root=repo,
        issue_text="fix it",
        trace=trace,
    )

    assert result["status"] == "finished"
    assert result["summary"] == "done"

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from patchproof.agents.baseline import BaselineAgent
from patchproof.agents.provider import OpenAIProvider
from patchproof.trace import TraceRecorder
from patchproof.workspace import prepare_workspace


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def run_baseline(
    case_id: str,
) -> dict:
    run_id = (
        f"{case_id}-baseline-"
        f"{uuid.uuid4().hex[:8]}"
    )

    workspace = prepare_workspace(
        case_id=case_id,
        run_id=run_id,
    )

    issue_text = workspace.issue_path.read_text(
        encoding="utf-8"
    )

    system_prompt = (
        PROJECT_ROOT
        / "prompts"
        / "baseline_system.md"
    ).read_text(
        encoding="utf-8"
    )

    trace_path = (
        PROJECT_ROOT
        / "evidence"
        / "traces"
        / f"{run_id}.jsonl"
    )

    trace = TraceRecorder(
        trace_path=trace_path,
        run_id=run_id,
        agent_name="baseline-agent",
    )

    provider = OpenAIProvider()

    agent = BaselineAgent(
        provider=provider,
        system_prompt=system_prompt,
        max_actions=16,
    )

    started = time.perf_counter()

    agent_result = agent.run(
        repository_root=workspace.repo,
        issue_text=issue_text,
        trace=trace,
    )

    elapsed = (
        time.perf_counter()
        - started
    )

    result = {
        "case_id": case_id,
        "run_id": run_id,
        "workspace": str(
            workspace.repo
        ),
        "trace": str(
            trace_path
        ),
        "wall_time_seconds": elapsed,
        "agent": agent_result,
    }

    run_metadata = (
        workspace.root
        / "run.json"
    )

    run_metadata.write_text(
        json.dumps(
            result,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return result

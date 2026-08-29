from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path

from patchproof.agents.protocol import (
    InvalidAgentAction,
    parse_agent_action,
)
from patchproof.agents.tools import execute_action
from patchproof.trace import TraceRecorder
from patchproof.workspace import prepare_workspace


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def print_agent_packet(
    system_prompt: str,
    issue_text: str,
    workspace_repo: Path,
) -> None:
    packet = {
        "instructions": system_prompt,
        "issue": issue_text,
        "workspace_note": (
            "You do not have direct filesystem access. "
            "Return exactly one JSON action at a time. "
            "A human relay will execute the action in the isolated "
            "workspace and return the tool result."
        ),
        "available_tools": [
            "list_files",
            "read_file",
            "search_text",
            "write_file",
            "run_command",
            "finish",
        ],
    }

    print("\n" + "=" * 72)
    print("BASELINE AGENT PACKET")
    print("=" * 72)
    print(json.dumps(packet, indent=2, ensure_ascii=False))
    print("=" * 72)
    print(f"Workspace: {workspace_repo}")
    print(
        "\nPaste the packet above into a NEW agent session that has "
        "never seen the hidden evaluator or this benchmark's solutions."
    )
    print()


def read_multiline_action() -> str:
    print("\nPaste ONE JSON action from the agent.")
    print("When finished, enter a line containing only: END")
    print()

    lines: list[str] = []

    while True:
        line = input()

        if line.strip() == "END":
            break

        lines.append(line)

    return "\n".join(lines).strip()


def run_manual_baseline(case_id: str) -> dict:
    run_id = (
        f"{case_id}-manual-baseline-"
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
        agent_name="manual-baseline-agent",
    )

    trace.record(
        "instruction",
        {
            "system_prompt": system_prompt,
            "issue": issue_text,
            "transport": "human-relay",
        },
    )

    print_agent_packet(
        system_prompt=system_prompt,
        issue_text=issue_text,
        workspace_repo=workspace.repo,
    )

    started = time.perf_counter()
    tool_actions = 0
    max_tool_actions = 16

    while tool_actions < max_tool_actions:
        raw = read_multiline_action()

        trace.record(
            "human_checkpoint",
            {
                "type": "relay_agent_action",
                "raw": raw,
            },
        )

        trace.record(
            "agent_message",
            raw,
        )

        try:
            action = parse_agent_action(raw)

        except InvalidAgentAction as exc:
            feedback = (
                "INVALID ACTION\n"
                f"{exc}\n\n"
                "Return exactly one valid JSON action."
            )

            trace.record(
                "evaluation_feedback",
                feedback,
            )

            print("\n" + "=" * 72)
            print("TOOL / VALIDATION RESULT TO RETURN TO AGENT")
            print("=" * 72)
            print(feedback)
            print("=" * 72)

            continue

        trace.record(
            "parsed_action",
            action,
        )

        if action["action"] == "finish":
            summary = action.get("summary", "")

            elapsed = time.perf_counter() - started

            trace.record(
                "final_result",
                {
                    "summary": summary,
                    "tool_actions": tool_actions,
                    "wall_time_seconds": elapsed,
                },
            )

            result = {
                "case_id": case_id,
                "run_id": run_id,
                "workspace": str(workspace.repo),
                "trace": str(trace_path),
                "status": "finished",
                "tool_actions": tool_actions,
                "wall_time_seconds": elapsed,
                "summary": summary,
            }

            run_file = workspace.root / "run.json"
            run_file.write_text(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            print("\n" + "=" * 72)
            print("MANUAL BASELINE FINISHED")
            print("=" * 72)
            print(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False,
                )
            )

            return result

        tool_actions += 1

        trace.record(
            "tool_call",
            action,
            tool_name=action["action"],
        )

        tool_result = execute_action(
            workspace.repo,
            action,
        )

        response = {
            "tool": action["action"],
            "ok": tool_result.ok,
            "output": tool_result.output,
            "metadata": tool_result.metadata,
        }

        trace.record(
            "tool_result",
            response,
            tool_name=action["action"],
        )

        trace.record(
            "human_checkpoint",
            {
                "type": "relay_tool_result_to_agent",
                "tool_action_number": tool_actions,
            },
        )

        print("\n" + "=" * 72)
        print("TOOL RESULT TO COPY BACK TO AGENT")
        print("=" * 72)
        print(
            json.dumps(
                response,
                indent=2,
                ensure_ascii=False,
            )
        )
        print("=" * 72)

    elapsed = time.perf_counter() - started

    trace.record(
        "final_result",
        {
            "summary": "Maximum tool-action budget reached",
            "tool_actions": tool_actions,
            "wall_time_seconds": elapsed,
        },
    )

    raise RuntimeError(
        f"Maximum tool-action budget reached: {max_tool_actions}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--case",
        required=True,
    )

    args = parser.parse_args()

    run_manual_baseline(
        case_id=args.case,
    )


if __name__ == "__main__":
    main()

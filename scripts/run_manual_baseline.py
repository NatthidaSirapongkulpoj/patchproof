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


def confirm_relay(
    trace: TraceRecorder,
    checkpoint_type: str,
) -> None:
    while True:
        confirmation = input(
            "\nAfter you have pasted the material into the "
            "agent session, type ACK: "
        ).strip()

        if confirmation == "ACK":
            trace.record(
                "human_checkpoint",
                {
                    "type": checkpoint_type,
                    "confirmed": True,
                },
            )
            return

        print("Please type exactly: ACK")


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
            "replace_text",
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
        "never seen the hidden evaluator or benchmark solutions."
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


def write_run_result(
    workspace,
    result: dict,
) -> None:
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

    confirm_relay(
        trace,
        "confirmed_initial_packet_relay",
    )

    started = time.perf_counter()
    tool_actions = 0
    max_tool_actions = 16

    while tool_actions < max_tool_actions:
        raw = read_multiline_action()

        if not raw:
            print(
                "\nNo action received. "
                "Paste one JSON action, then enter END."
            )
            continue

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
            print("VALIDATION RESULT TO COPY BACK TO AGENT")
            print("=" * 72)
            print(feedback)
            print("=" * 72)

            confirm_relay(
                trace,
                "confirmed_validation_feedback_relay",
            )

            continue

        trace.record(
            "parsed_action",
            action,
        )

        if action["action"] == "finish":
            summary = action["summary"]
            elapsed = time.perf_counter() - started

            trace.record(
                "final_result",
                {
                    "summary": summary,
                    "tool_actions": tool_actions,
                    "wall_time_seconds": elapsed,
                    "status": "finished",
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
                "transport": "human-relay-with-ack",
            }

            write_run_result(
                workspace,
                result,
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

        confirm_relay(
            trace,
            "confirmed_tool_result_relay",
        )

    elapsed = time.perf_counter() - started
    summary = "Maximum tool-action budget reached"

    trace.record(
        "final_result",
        {
            "summary": summary,
            "tool_actions": tool_actions,
            "wall_time_seconds": elapsed,
            "status": "action_limit",
        },
    )

    result = {
        "case_id": case_id,
        "run_id": run_id,
        "workspace": str(workspace.repo),
        "trace": str(trace_path),
        "status": "action_limit",
        "tool_actions": tool_actions,
        "wall_time_seconds": elapsed,
        "summary": summary,
        "transport": "human-relay-with-ack",
    }

    write_run_result(
        workspace,
        result,
    )

    print("\n" + "=" * 72)
    print("MANUAL BASELINE ENDED AT ACTION LIMIT")
    print("=" * 72)
    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )

    return result


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

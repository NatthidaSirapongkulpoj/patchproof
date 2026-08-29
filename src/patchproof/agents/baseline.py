from __future__ import annotations

from pathlib import Path

from patchproof.agents.protocol import (
    InvalidAgentAction,
    parse_agent_action,
)
from patchproof.agents.provider import ModelProvider
from patchproof.agents.tools import execute_action
from patchproof.trace import TraceRecorder


class BaselineAgent:
    def __init__(
        self,
        provider: ModelProvider,
        system_prompt: str,
        max_actions: int = 16,
    ) -> None:
        self.provider = provider
        self.system_prompt = system_prompt
        self.max_actions = max_actions

    def run(
        self,
        repository_root: Path,
        issue_text: str,
        trace: TraceRecorder,
    ) -> dict:
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": (
                    "Repair the following issue.\n\n"
                    f"{issue_text}"
                ),
            },
        ]

        trace.record(
            "instruction",
            {
                "system_prompt": self.system_prompt,
                "issue": issue_text,
            },
        )

        total_input_tokens = 0
        total_output_tokens = 0

        for _ in range(self.max_actions):
            response = self.provider.generate(
                messages
            )

            total_input_tokens += (
                response.input_tokens or 0
            )

            total_output_tokens += (
                response.output_tokens or 0
            )

            trace.record(
                "agent_message",
                response.text,
                metadata={
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                },
            )

            try:
                action = parse_agent_action(
                    response.text
                )

            except InvalidAgentAction as exc:
                feedback = (
                    "Your previous response was invalid. "
                    "Return exactly one valid JSON action. "
                    f"Error: {exc}"
                )

                messages.append(
                    {
                        "role": "assistant",
                        "content": response.text,
                    }
                )

                messages.append(
                    {
                        "role": "user",
                        "content": feedback,
                    }
                )

                trace.record(
                    "evaluation_feedback",
                    feedback,
                )

                continue

            trace.record(
                "parsed_action",
                action,
            )

            if action["action"] == "finish":
                summary = action.get(
                    "summary",
                    "",
                )

                trace.record(
                    "final_result",
                    {
                        "summary": summary,
                    },
                )

                return {
                    "status": "finished",
                    "summary": summary,
                    "tool_actions": trace.step,
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                }

            trace.record(
                "tool_call",
                action,
                tool_name=action["action"],
            )

            result = execute_action(
                repository_root,
                action,
            )

            trace.record(
                "tool_result",
                {
                    "ok": result.ok,
                    "output": result.output,
                    "metadata": result.metadata,
                },
                tool_name=action["action"],
            )

            messages.append(
                {
                    "role": "assistant",
                    "content": response.text,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Tool result:\n"
                        f"ok={result.ok}\n"
                        f"{result.output}"
                    ),
                }
            )

        trace.record(
            "final_result",
            {
                "summary": (
                    "Maximum action budget reached"
                )
            },
        )

        return {
            "status": "action_limit",
            "summary": (
                "Maximum action budget reached"
            ),
            "tool_actions": trace.step,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
        }

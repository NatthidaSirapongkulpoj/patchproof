from __future__ import annotations

import subprocess
from pathlib import Path

from patchproof.models import ToolResult


ALLOWED_COMMAND_PREFIXES = (
    "pytest",
    "python -m pytest",
    "python",
)


def run_command(
    repository_root: Path,
    command: str,
    timeout_seconds: int = 60,
) -> ToolResult:
    command = command.strip()

    if not command.startswith(
        ALLOWED_COMMAND_PREFIXES
    ):
        return ToolResult(
            ok=False,
            output=(
                "Command rejected by sandbox policy: "
                f"{command}"
            ),
        )

    try:
        result = subprocess.run(
            command,
            cwd=repository_root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=True,
        )

        output = (
            result.stdout
            + (
                "\n" + result.stderr
                if result.stderr
                else ""
            )
        )

        return ToolResult(
            ok=result.returncode == 0,
            output=output,
            metadata={
                "exit_code": result.returncode,
            },
        )

    except subprocess.TimeoutExpired:
        return ToolResult(
            ok=False,
            output=(
                f"Command timed out after "
                f"{timeout_seconds} seconds"
            ),
            metadata={
                "timed_out": True,
            },
        )

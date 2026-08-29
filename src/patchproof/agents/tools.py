from __future__ import annotations

from pathlib import Path

from patchproof.models import ToolResult
from patchproof.tools.files import (
    list_files,
    read_file,
)
from patchproof.tools.patch import (
    replace_text,
    write_file,
)
from patchproof.tools.search import search_text
from patchproof.tools.shell import run_command


def execute_action(
    repository_root: Path,
    action: dict,
) -> ToolResult:
    kind = action["action"]

    if kind == "list_files":
        return list_files(
            repository_root,
            action.get("path", "."),
        )

    if kind == "read_file":
        return read_file(
            repository_root,
            action["path"],
        )

    if kind == "search_text":
        return search_text(
            repository_root,
            action["query"],
        )

    if kind == "write_file":
        return write_file(
            repository_root,
            action["path"],
            action["content"],
        )

    if kind == "replace_text":
        return replace_text(
            repository_root,
            action["path"],
            action["old"],
            action["new"],
        )

    if kind == "run_command":
        return run_command(
            repository_root,
            action["command"],
        )

    return ToolResult(
        ok=False,
        output=f"Action is not a tool call: {kind}",
    )

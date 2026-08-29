from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ToolResult:
    ok: bool
    output: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentAction:
    kind: str
    arguments: dict[str, Any]


@dataclass
class RepairRun:
    case_id: str
    run_id: str
    workspace_root: Path
    repository_path: Path
    issue_path: Path
    mode: str
    status: str = "created"
    tool_actions: int = 0
    final_message: str | None = None

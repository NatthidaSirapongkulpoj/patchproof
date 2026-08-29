from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_CASES = PROJECT_ROOT / "benchmark" / "cases"
RUNS_ROOT = PROJECT_ROOT / ".patchproof" / "runs"


@dataclass(frozen=True)
class RepairWorkspace:
    case_id: str
    run_id: str
    root: Path
    repo: Path
    issue_path: Path


def prepare_workspace(
    case_id: str,
    run_id: str,
) -> RepairWorkspace:
    case_root = BENCHMARK_CASES / case_id

    if not case_root.exists():
        raise FileNotFoundError(
            f"Unknown benchmark case: {case_id}"
        )

    source_repo = case_root / "repo"
    source_issue = case_root / "issue.md"

    run_root = RUNS_ROOT / run_id
    workspace_repo = run_root / "repo"
    workspace_issue = run_root / "issue.md"

    if run_root.exists():
        shutil.rmtree(run_root)

    run_root.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        source_repo,
        workspace_repo,
    )

    shutil.copy2(
        source_issue,
        workspace_issue,
    )

    return RepairWorkspace(
        case_id=case_id,
        run_id=run_id,
        root=run_root,
        repo=workspace_repo,
        issue_path=workspace_issue,
    )

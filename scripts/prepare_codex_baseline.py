from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from patchproof.workspace import prepare_workspace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_TEMPLATE = PROJECT_ROOT / "prompts" / "codex_baseline.md"
VALID_CASES = {f"PP-{number:02d}" for number in range(1, 13)}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def prepare_codex_run(case_id: str) -> dict:
    if case_id not in VALID_CASES:
        raise ValueError("case ID must be one of PP-01 through PP-12")

    run_id = f"{case_id}-codex-baseline-{uuid.uuid4().hex[:8]}"
    workspace = prepare_workspace(case_id=case_id, run_id=run_id)
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8").rstrip()
    issue = workspace.issue_path.read_text(encoding="utf-8").rstrip()
    prompt_path = workspace.root / "codex-prompt.md"
    prompt_path.write_text(
        f"{template}\n\nIssue supplied with the workspace:\n\n{issue}\n",
        encoding="utf-8",
    )

    metadata = {
        "case_id": case_id,
        "run_id": run_id,
        "execution_mode": "codex-cli",
        "model": "gpt-5.6-sol",
        "benchmark_tag": "benchmark-v1",
        "baseline_prompt_version": "codex-baseline-v1",
        "created_at": utc_now(),
        "status": "prepared",
        "repo_path": str(workspace.repo.resolve()),
        "prompt_path": str(prompt_path.resolve()),
    }
    metadata_path = workspace.root / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return metadata


def launch_command(metadata: dict) -> str:
    prompt = str(metadata["prompt_path"]).replace("'", "''")
    repo = str(metadata["repo_path"]).replace("'", "''")
    return (
        f"Get-Content -Raw -LiteralPath '{prompt}' | "
        "codex exec --model gpt-5.6-sol --sandbox workspace-write "
        f"--cd '{repo}' -"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, choices=sorted(VALID_CASES))
    args = parser.parse_args()
    metadata = prepare_codex_run(args.case)
    print(f"run_id: {metadata['run_id']}")
    print(f"repo path: {metadata['repo_path']}")
    print(f"prompt file path: {metadata['prompt_path']}")
    print("Launch Codex from the isolated repo with this PowerShell command:")
    print(launch_command(metadata))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import shutil
import uuid
from pathlib import Path

from patchproof.final.models import RunMetadata
from patchproof.workspace import prepare_workspace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALID_CASES = {f"PP-{number:02d}" for number in range(1, 13)}
PROMPT_NAMES = ("investigator", "repair_agent", "verifier", "evidence_reporter")


def _quote(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def codex_command(prompt: Path, repo: Path, run_root: Path, artifact: Path, *, writable: bool) -> str:
    sandbox = "workspace-write" if writable else "read-only"
    return (
        f"Get-Content -Raw -LiteralPath '{_quote(prompt)}' | "
        f"codex exec --model gpt-5.6-sol --sandbox {sandbox} --skip-git-repo-check "
        f"--add-dir '{_quote(run_root)}' --output-last-message '{_quote(artifact)}' "
        f"--cd '{_quote(repo)}' -"
    )


def prepare_final_run(case_id: str) -> dict:
    if case_id not in VALID_CASES:
        raise ValueError("case ID must be one of PP-01 through PP-12")
    run_id = f"{case_id}-patchproof-final-{uuid.uuid4().hex[:8]}"
    workspace = prepare_workspace(case_id, run_id)
    artifact_root = workspace.root / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    pristine_app = workspace.root / "pristine-app"
    shutil.copytree(workspace.repo / "app", pristine_app)
    prompts: dict[str, str] = {}
    commands: dict[str, str] = {}
    issue = workspace.issue_path.read_text(encoding="utf-8").rstrip()
    for name in PROMPT_NAMES:
        template = (PROJECT_ROOT / "prompts" / f"{name}.md").read_text(encoding="utf-8").rstrip()
        destination = workspace.root / f"{name}-prompt.md"
        artifact = artifact_root / f"{name}.json"
        destination.write_text(
            f"{template}\n\nCase: {case_id}\nIssue:\n{issue}\n\n"
            f"Isolated repository: {workspace.repo.resolve()}\n"
            f"Write the requested artifact to: {artifact.resolve()}\n"
            f"Pristine app reference for diff inspection: {pristine_app.resolve()}\n"
            f"Trajectory path: {(workspace.root / 'trajectory.jsonl').resolve()}\n",
            encoding="utf-8",
        )
        prompts[name] = str(destination.resolve())
        commands[name] = codex_command(
            destination,
            workspace.repo,
            workspace.root,
            artifact,
            writable=name == "repair_agent",
        )
    metadata = RunMetadata(run_id=run_id, case_id=case_id).to_dict()
    metadata.update(
        {
            "repo_path": str(workspace.repo.resolve()),
            "issue_path": str(workspace.issue_path.resolve()),
            "artifact_root": str(artifact_root.resolve()),
            "pristine_app_path": str(pristine_app.resolve()),
            "trace_path": str((workspace.root / "trajectory.jsonl").resolve()),
            "prompts": prompts,
            "commands": commands,
        }
    )
    (workspace.root / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, choices=sorted(VALID_CASES))
    args = parser.parse_args()
    metadata = prepare_final_run(args.case)
    print(json.dumps({
        "run_id": metadata["run_id"],
        "run_command": f"python scripts/run_patchproof_final.py --run-id {metadata['run_id']}",
        "helpful_stage_commands": metadata["commands"],
    }, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from patchproof.workspace import RUNS_ROOT


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = PROJECT_ROOT / "evidence" / "baseline-codex"
EVALUATOR = PROJECT_ROOT / "benchmark" / "evaluator" / "run_case.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def evaluate_codex_run(run_id: str) -> dict:
    run_root = RUNS_ROOT / run_id
    metadata_path = run_root / "metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"prepared run metadata not found: {run_id}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("run_id") != run_id or metadata.get("status") != "prepared":
        raise ValueError(f"run is not a matching prepared run: {run_id}")
    case_id = metadata["case_id"]
    repo = Path(metadata["repo_path"]).resolve()
    if repo != (run_root / "repo").resolve() or not repo.is_dir():
        raise ValueError("metadata repo path is not the prepared run repository")

    process = subprocess.run(
        [
            sys.executable,
            str(EVALUATOR),
            "--case",
            case_id,
            "--workspace",
            str(repo),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(
            "evaluator failed before producing a result\n"
            f"stdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("evaluator stdout was not valid JSON") from exc

    result["run_id"] = run_id
    result["benchmark_tag"] = metadata["benchmark_tag"]
    result["baseline_prompt_version"] = metadata["baseline_prompt_version"]
    result["execution_mode"] = metadata["execution_mode"]
    result["model"] = metadata["model"]
    result["evaluator_process"] = {
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    evidence_path = EVIDENCE_ROOT / f"{case_id}-{run_id}.json"
    evidence_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    gates = result["gates"]
    metadata.update(
        {
            "status": "evaluated",
            "evaluated_at": utc_now(),
            "success": result["success"],
            "visible_tests": gates["visible_tests"],
            "hidden_acceptance": gates["hidden_acceptance"],
            "patch_policy": gates["patch_policy"],
            "timeout": gates["timeout"],
            "changed_files": result["policy"]["changed_files"],
            "evidence_path": str(evidence_path.resolve()),
        }
    )
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    result = evaluate_codex_run(args.run_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

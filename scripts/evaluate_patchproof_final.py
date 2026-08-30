from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from patchproof.final.evidence import read_records
from patchproof.final.vrrr import compute_vrrr_gates
from patchproof.workspace import RUNS_ROOT


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = PROJECT_ROOT / "benchmark" / "evaluator" / "run_case.py"
EVIDENCE_ROOT = PROJECT_ROOT / "evidence" / "final"
TRACE_ROOT = PROJECT_ROOT / "evidence" / "final-traces"


def evaluate_final_run(run_id: str) -> dict:
    run_root = RUNS_ROOT / run_id
    metadata_path = run_root / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("run_id") != run_id or metadata.get("status") != "workflow_completed":
        raise ValueError("hidden evaluator may run only after workflow completion")
    repo = Path(metadata["repo_path"]).resolve()
    if repo != (run_root / "repo").resolve():
        raise ValueError("metadata repository is not the isolated run repository")
    review_path = Path(metadata["artifact_root"]) / "evidence_reporter.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    trajectory = read_records(Path(metadata["trace_path"]))

    process = subprocess.run(
        [sys.executable, str(EVALUATOR), "--case", metadata["case_id"], "--workspace", str(repo)],
        cwd=PROJECT_ROOT, capture_output=True, text=True, check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(f"evaluator failed: {process.stderr}")
    evaluator = json.loads(process.stdout)
    gates = compute_vrrr_gates(
        hidden_evaluator_result={"passed": evaluator["gates"]["hidden_acceptance"]},
        visible_evaluator_result={"passed": evaluator["gates"]["visible_tests"]},
        policy_evaluator_result={"passed": evaluator["gates"]["patch_policy"]},
        trajectory=trajectory,
        review_artifact=review,
    )
    result = {
        **{key: metadata[key] for key in ("run_id", "case_id", "benchmark_tag", "execution_mode", "model", "workflow_version", "created_at")},
        "status": "evaluated",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "success": bool(evaluator["success"]),
        "gates": gates,
        "review_artifact": {**review, "ready_for_human_review": gates["review_ready"]},
        "evaluator": evaluator,
    }
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    TRACE_ROOT.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_ROOT / f"{metadata['case_id']}-{run_id}.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (TRACE_ROOT / f"{run_id}.jsonl").write_text(
        Path(metadata["trace_path"]).read_text(encoding="utf-8"), encoding="utf-8"
    )
    metadata.update({"status": "evaluated", "ready_for_human_review": gates["review_ready"]})
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate_final_run(args.run_id), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

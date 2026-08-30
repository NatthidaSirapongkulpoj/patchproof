from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = PROJECT_ROOT / "evidence" / "final"
SUMMARY_PATH = PROJECT_ROOT / "evidence" / "patchproof-final-summary.json"
ALL_CASES = [f"PP-{number:02d}" for number in range(1, 13)]


def summarize(evidence_root: Path = EVIDENCE_ROOT) -> dict:
    by_case: dict[str, dict] = {}
    for path in sorted(evidence_root.glob("*.json")) if evidence_root.exists() else []:
        result = json.loads(path.read_text(encoding="utf-8"))
        case_id = result.get("case_id")
        if case_id not in ALL_CASES:
            raise ValueError(f"invalid case_id in {path}: {case_id}")
        if case_id in by_case:
            raise ValueError(f"duplicate official final results for {case_id}")
        by_case[case_id] = result
    rows = []
    for case_id in ALL_CASES:
        if case_id in by_case:
            item = by_case[case_id]
            rows.append({"case_id": case_id, "run_id": item.get("run_id"), "success": bool(item.get("success")), **item.get("gates", {})})
    evaluated = len(rows)
    successes = sum(row["success"] for row in rows)
    ready = sum(bool(row.get("review_ready")) for row in rows)
    return {
        "evaluated_case_count": evaluated,
        "successful_case_count": successes,
        "review_ready_case_count": ready,
        "vtsr_percentage": (successes / evaluated * 100.0) if evaluated else 0.0,
        "vrrr_percentage": (ready / evaluated * 100.0) if evaluated else 0.0,
        "missing_cases": [case for case in ALL_CASES if case not in by_case],
        "per_case_gates": rows,
    }


def write_summary(evidence_root: Path = EVIDENCE_ROOT, summary_path: Path = SUMMARY_PATH) -> dict:
    result = summarize(evidence_root)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    argparse.ArgumentParser().parse_args()
    print(json.dumps(write_summary(), indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = PROJECT_ROOT / "evidence" / "baseline-codex"
SUMMARY_PATH = PROJECT_ROOT / "evidence" / "baseline-codex-summary.json"
ALL_CASES = [f"PP-{number:02d}" for number in range(1, 13)]
GATE_NAMES = ("visible_tests", "hidden_acceptance", "patch_policy", "timeout")


def summarize(evidence_root: Path = EVIDENCE_ROOT) -> dict:
    by_case: dict[str, dict] = {}
    for path in sorted(evidence_root.glob("*.json")) if evidence_root.exists() else []:
        result = json.loads(path.read_text(encoding="utf-8"))
        case_id = result.get("case_id")
        if case_id not in ALL_CASES:
            raise ValueError(f"invalid case_id in {path}: {case_id}")
        if case_id in by_case:
            raise ValueError(f"duplicate official results for {case_id}")
        by_case[case_id] = result

    table = []
    for case_id in ALL_CASES:
        if case_id not in by_case:
            continue
        result = by_case[case_id]
        gates = result.get("gates", {})
        table.append(
            {
                "case_id": case_id,
                "run_id": result.get("run_id"),
                **{name: bool(gates.get(name, False)) for name in GATE_NAMES},
                "success": bool(result.get("success", False)),
            }
        )

    successes = sum(row["success"] for row in table)
    evaluated = len(table)
    return {
        "evaluated_case_count": evaluated,
        "successful_case_count": successes,
        "failed_case_count": evaluated - successes,
        "vtsr_percentage": (successes / evaluated * 100.0) if evaluated else 0.0,
        "missing_cases": [case for case in ALL_CASES if case not in by_case],
        "per_case_gates": table,
    }


def write_summary(
    evidence_root: Path = EVIDENCE_ROOT,
    summary_path: Path = SUMMARY_PATH,
) -> dict:
    result = summarize(evidence_root)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    result = write_summary()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

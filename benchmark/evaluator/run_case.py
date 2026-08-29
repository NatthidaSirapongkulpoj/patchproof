from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_pytest(
    cwd: Path,
    test_path: Path,
    timeout_seconds: int = 60,
) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd)

    started = time.perf_counter()

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                str(test_path),
            ],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        elapsed = time.perf_counter() - started

        return {
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "timed_out": False,
            "duration_seconds": elapsed,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - started

        return {
            "passed": False,
            "exit_code": None,
            "timed_out": True,
            "duration_seconds": elapsed,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }


def evaluate_case(case_id: str) -> dict:
    repo = ROOT / "benchmark" / "cases" / case_id / "repo"

    visible_tests = repo / "tests"

    hidden_tests = (
        ROOT
        / "benchmark"
        / "evaluator"
        / "oracles"
        / case_id
    )

    if not repo.exists():
        raise FileNotFoundError(
            f"Unknown benchmark case: {case_id}"
        )

    visible = run_pytest(
        cwd=repo,
        test_path=visible_tests,
    )

    hidden = run_pytest(
        cwd=repo,
        test_path=hidden_tests,
    )

    success = (
        visible["passed"]
        and hidden["passed"]
        and not visible["timed_out"]
        and not hidden["timed_out"]
    )

    return {
        "case_id": case_id,
        "success": success,
        "gates": {
            "visible_tests": visible["passed"],
            "hidden_acceptance": hidden["passed"],
        },
        "visible": visible,
        "hidden": hidden,
    }


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--case",
        required=True,
    )

    parser.add_argument(
        "--out",
        required=False,
    )

    args = parser.parse_args()

    result = evaluate_case(args.case)

    text = json.dumps(
        result,
        indent=2,
        ensure_ascii=False,
    )

    print(text)

    if args.out:
        out_path = Path(args.out)

        out_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        out_path.write_text(
            text + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()

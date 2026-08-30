from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .models import VerificationDecision


def run_visible_tests(repo: Path, timeout_seconds: int = 60) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(repo / "tests")],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "passed": False,
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }


def require_explicit_verifier_pass(records: list[dict]) -> bool:
    return any(
        record.get("role") == "verifier"
        and record.get("event_type") == "decision"
        and record.get("decision") == "pass"
        and bool(record.get("evidence_id"))
        for record in records
    )


def validate_decision(decision: VerificationDecision) -> None:
    decision.validate()

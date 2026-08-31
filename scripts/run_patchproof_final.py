from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import MISSING, fields
from pathlib import Path
from typing import Any

from patchproof.final.evidence import (
    append_record,
    evidence_integrity_pass,
    read_records,
    review_artifact_complete,
)
from patchproof.final.investigator import production_snapshot, validate_investigation
from patchproof.final.models import (
    InvestigationArtifact,
    ReviewArtifact,
    TrajectoryRecord,
    VerificationDecision,
    utc_now,
)
from patchproof.workspace import RUNS_ROOT


MODEL = "gpt-5.6-sol"
MAX_REPAIR_ATTEMPTS = 2
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_codex_executable() -> str:
    """Return the platform-appropriate Codex executable path."""
    candidates = ("codex.cmd", "codex") if os.name == "nt" else ("codex",)
    for candidate in candidates:
        executable = shutil.which(candidate)
        if executable:
            return executable
    searched = " or ".join(candidates)
    raise RuntimeError(f"Codex executable not found on PATH (looked for {searched})")


def _record(trace: Path, role: str, attempt: int, event_type: str, **values: Any) -> None:
    append_record(trace, TrajectoryRecord(
        timestamp=utc_now(), role=role, attempt=attempt, event_type=event_type, **values
    ))


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} did not produce valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} artifact must be a JSON object")
    return value


def _dataclass_from_dict(cls: type, value: dict[str, Any], label: str):
    expected = {item.name for item in fields(cls)}
    unknown = set(value) - expected
    missing = {
        item.name for item in fields(cls)
        if item.default is MISSING and item.default_factory is MISSING
    } - set(value)
    if unknown or missing:
        raise RuntimeError(f"invalid {label} fields; missing={sorted(missing)}, unknown={sorted(unknown)}")
    try:
        return cls(**value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"invalid {label}: {exc}") from exc


def _review_artifact_fields() -> tuple[str, ...]:
    """Return the canonical top-level schema owned by ReviewArtifact."""
    return tuple(item.name for item in fields(ReviewArtifact))


def _normalize_review_artifact(
    value: dict[str, Any], trace: Path, attempt: int,
) -> tuple[ReviewArtifact, dict[str, Any]]:
    """Discard only unknown top-level metadata, recording every discarded key."""
    allowed = _review_artifact_fields()
    unknown = sorted(set(value) - set(allowed))
    canonical = {name: value[name] for name in allowed if name in value}
    if unknown:
        _record(
            trace, "evidence_reporter", attempt, "review_artifact_normalized",
            output=json.dumps({"discarded_top_level_fields": unknown}, ensure_ascii=False),
        )

    review = _dataclass_from_dict(ReviewArtifact, canonical, "review artifact")
    string_fields = (
        "root_cause", "behavior_fixed", "remaining_risk", "human_review_action",
    )
    if any(not isinstance(getattr(review, name), str) for name in string_fields):
        raise RuntimeError("invalid review artifact: required text fields must be strings")
    if not isinstance(review.changed_files, list) or any(
        not isinstance(item, str) for item in review.changed_files
    ):
        raise RuntimeError("invalid review artifact: changed_files must be a list of strings")
    for name in ("verification_performed", "verification_results"):
        claims = getattr(review, name)
        if not isinstance(claims, list) or any(
            not isinstance(claim, dict)
            or any(not isinstance(key, str) or not isinstance(item, str)
                   for key, item in claim.items())
            for claim in claims
        ):
            raise RuntimeError(
                f"invalid review artifact: {name} must be a list of string-to-string objects"
            )
    if not isinstance(review.ready_for_human_review, bool):
        raise RuntimeError("invalid review artifact: ready_for_human_review must be a boolean")
    return review, canonical


def _command(repo: Path, run_root: Path, artifact: Path, writable: bool) -> list[str]:
    return [
        resolve_codex_executable(), "exec", "--model", MODEL, "--sandbox",
        "workspace-write" if writable else "read-only", "--skip-git-repo-check",
        "--add-dir", str(run_root), "--output-last-message", str(artifact),
        "--cd", str(repo), "-",
    ]


def _invoke(
    trace: Path, role: str, attempt: int, repo: Path, run_root: Path,
    artifact: Path, prompt: str, writable: bool, evidence_id: str | None = None,
) -> None:
    command = _command(repo, run_root, artifact, writable)
    shown = subprocess.list2cmdline(command)
    try:
        process = subprocess.run(
            command, input=prompt, text=True, encoding="utf-8", errors="strict",
            capture_output=True, check=False, cwd=repo, shell=False,
        )
    except OSError as exc:
        output = json.dumps({"exception": str(exc)}, ensure_ascii=False)
        _record(trace, role, attempt, "command_result", command=shown, output=output,
                exit_code=-1, evidence_id=evidence_id)
        raise RuntimeError(f"{role} Codex subprocess could not be created: {exc}") from exc
    output = json.dumps({"stdout": process.stdout, "stderr": process.stderr}, ensure_ascii=False)
    _record(trace, role, attempt, "command_result", command=shown, output=output,
            exit_code=process.returncode, evidence_id=evidence_id)
    if process.returncode != 0:
        raise RuntimeError(f"{role} Codex subprocess exited {process.returncode}: {process.stderr}")
    if not artifact.is_file():
        raise RuntimeError(f"{role} Codex subprocess did not produce its required artifact")


def _changed(before: dict[str, bytes], after: dict[str, bytes]) -> list[str]:
    return sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))


def _read_prompt(metadata: dict[str, Any], role: str) -> str:
    return Path(metadata["prompts"][role]).read_text(encoding="utf-8")


def _finish_with_evidence_reporter(
    metadata: dict[str, Any], metadata_path: Path, run_root: Path, repo: Path,
    trace: Path, artifacts: Path, investigation_path: Path, verifier_path: Path,
    attempt: int, decision: VerificationDecision,
) -> None:
    review_path = artifacts / "evidence_reporter.json"
    raw_review_path = artifacts / "evidence_reporter.raw.json"
    reporter_prompt = _read_prompt(metadata, "evidence_reporter") + (
        "\n\nUse the actual artifacts and trajectory supplied in this run. "
        f"Investigation: {investigation_path}. Repair attempts: {attempt}. "
        f"Final verifier artifact: {verifier_path}. Trajectory: {trace}. "
        "Reference only evidence_id values that already occur in the trajectory."
    )
    reporter_before = production_snapshot(repo)
    _record(trace, "evidence_reporter", attempt, "stage_started")
    _invoke(trace, "evidence_reporter", attempt, repo, run_root, raw_review_path, reporter_prompt, False)
    if production_snapshot(repo) != reporter_before:
        raise RuntimeError("evidence reporter modified repository files")
    raw_review_data = _load_object(raw_review_path, "evidence reporter")
    review, review_data = _normalize_review_artifact(raw_review_data, trace, attempt)
    if not review_artifact_complete(review_data) or review.ready_for_human_review:
        raise RuntimeError("review artifact is incomplete or prematurely claims readiness")
    if not evidence_integrity_pass(review_data, read_records(trace)):
        raise RuntimeError("review artifact contains missing trajectory evidence references")
    review_path.write_text(
        json.dumps(review_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _record(trace, "evidence_reporter", attempt, "artifact", output=json.dumps(review_data),
            evidence_id="review-artifact")
    _record(trace, "evidence_reporter", attempt, "stage_completed")
    _record(trace, "workflow", attempt, "human_review_checkpoint",
            output="No merge or deployment occurred; human review is required.", decision="required")
    _record(trace, "workflow", attempt, "workflow_completed",
            decision="verification_passed" if decision.passed else "verification_failed")
    metadata["status"] = "workflow_completed"
    metadata["verification_status"] = "passed" if decision.passed else "failed"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _is_generated_app_file(name: str) -> bool:
    return "/__pycache__/" in f"/{name}" or name.endswith((".pyc", ".pyo"))


def _feedback_items(decision: VerificationDecision) -> list[str]:
    return ([decision.retry_feedback] if isinstance(decision.retry_feedback, str)
            else list(decision.retry_feedback)) or list(decision.findings)


def resume_after_verifier(run_id: str) -> VerificationDecision:
    run_root = (RUNS_ROOT / run_id).resolve()
    if run_root.parent != RUNS_ROOT.resolve():
        raise ValueError("unsafe run ID")
    metadata_path = run_root / "metadata.json"
    metadata = _load_object(metadata_path, "metadata")
    if metadata.get("run_id") != run_id or metadata.get("status") != "prepared":
        raise ValueError("recovery requires an existing prepared run")
    if metadata.get("workflow_version") != "patchproof-final-v2":
        raise ValueError("only patchproof-final-v2 runs may use verifier recovery")
    repo = Path(metadata["repo_path"]).resolve()
    trace = Path(metadata["trace_path"])
    artifacts = Path(metadata["artifact_root"])
    pristine = Path(metadata["pristine_app_path"])
    if repo != (run_root / "repo").resolve() or not trace.is_file():
        raise ValueError("recovery requires the isolated repository and existing trajectory")
    investigation_path = artifacts / "investigator.json"
    repairs = sorted(artifacts.glob("repair_agent-attempt-*.txt"))
    verifiers = sorted(artifacts.glob("verifier-attempt-*.json"))
    if not investigation_path.is_file() or len(repairs) != 1 or len(verifiers) != 1:
        raise ValueError("recovery requires exactly one investigation, repair, and verifier artifact")
    if any((artifacts / name).exists() for name in (
        "evidence_reporter.json", "evidence_reporter.raw.json"
    )):
        raise ValueError("evidence reporter already ran; recovery state is ambiguous")
    records = read_records(trace)
    if any(item.get("event_type") == "workflow_completed" for item in records):
        raise ValueError("workflow already completed")
    if any(item.get("role") == "evidence_reporter" for item in records):
        raise ValueError("evidence reporter already ran; recovery state is ambiguous")
    final_dir = PROJECT_ROOT / "evidence" / "final"
    if any(final_dir.glob(f"*{run_id}*.json")) or any(
        token in path.name.lower() for path in run_root.rglob("*.json")
        for token in ("hidden", "evaluation-result", "evaluator-result")
    ):
        raise ValueError("hidden evaluation result already exists")
    attempt = int(verifiers[0].stem.rsplit("-", 1)[-1])
    decision_data = _load_object(verifiers[0], "verifier")
    decision = _dataclass_from_dict(VerificationDecision, decision_data, "verifier decision")
    decision.validate()
    allowed = {f"visible-tests-attempt-{attempt}", f"contract-check-attempt-{attempt}"}
    if not set(decision.verification_evidence_ids) <= allowed:
        raise RuntimeError("verifier referenced non-deterministic or unavailable evidence")
    repair_events = [item for item in records if item.get("role") == "repair_agent"
                     and item.get("event_type") == "attempt_completed"]
    if len(repair_events) != 1 or repair_events[0].get("attempt") != attempt:
        raise ValueError("trajectory does not contain one matching completed repair")
    try:
        recorded_changed = sorted(json.loads(repair_events[0]["output"]))
    except (TypeError, json.JSONDecodeError):
        raise ValueError("recorded repair change set is ambiguous") from None
    current_changed = _changed(production_snapshot(pristine), production_snapshot(repo / "app"))
    current_changed = [f"app/{name}" for name in current_changed]
    if current_changed != recorded_changed:
        raise ValueError("current app tree does not match the recorded repair change set")
    inspected = {name.replace("\\", "/").lstrip("./") for name in decision.inspected_files}
    material_changed = {name for name in current_changed if not _is_generated_app_file(name)}
    if not material_changed or not material_changed <= inspected:
        raise ValueError("verifier did not inspect every material repaired app file")
    verifier_mtime = verifiers[0].stat().st_mtime_ns
    if any(path.stat().st_mtime_ns > verifier_mtime for path in (repo / "app").rglob("*") if path.is_file()):
        raise ValueError("app tree contains files modified after verifier inspection")
    audit = {
        "reason": "recovery from a harness validation defect",
        "repair_or_verifier_rerun": False,
        "existing_observed_verifier_result_reused": True,
        "hidden_evaluation_had_run": False,
    }
    _record(trace, "workflow", attempt, "recovery_started", output=json.dumps(audit))
    _record(trace, "verifier", attempt, "artifact", output=json.dumps(decision_data),
            evidence_id=f"contract-check-attempt-{attempt}")
    _record(trace, "verifier", attempt, "verifier_decision_recovered",
            output=json.dumps({
                **audit,
                "statement": (
                    "Recovery from a harness validation defect; no repair or verifier rerun "
                    "occurred; the existing observed verifier result was reused; hidden "
                    "evaluation had not run."
                ),
                "verifier_artifact": str(verifiers[0]),
            }),
            decision="pass" if decision.passed else "fail")
    _record(trace, "verifier", attempt, "decision", output=json.dumps(decision_data),
            decision="pass" if decision.passed else "fail",
            evidence_id=f"verifier-decision-attempt-{attempt}")
    _finish_with_evidence_reporter(metadata, metadata_path, run_root, repo, trace, artifacts,
                                   investigation_path, verifiers[0], attempt, decision)
    return decision


def run_final_workflow(run_id: str) -> VerificationDecision:
    run_root = (RUNS_ROOT / run_id).resolve()
    if run_root.parent != RUNS_ROOT.resolve():
        raise ValueError("unsafe run ID")
    metadata_path = run_root / "metadata.json"
    metadata = _load_object(metadata_path, "metadata")
    if metadata.get("run_id") != run_id or metadata.get("status") != "prepared":
        raise ValueError("run must exist and have status prepared")
    if metadata.get("workflow_version") != "patchproof-final-v2":
        raise ValueError("only patchproof-final-v2 runs may use this runner")
    repo = Path(metadata["repo_path"]).resolve()
    if repo != (run_root / "repo").resolve():
        raise ValueError("metadata repository is not the isolated run repository")
    trace = Path(metadata["trace_path"])
    artifacts = Path(metadata["artifact_root"])
    if trace.exists():
        raise ValueError("trajectory already exists; refusing to rewrite run evidence")

    investigation_path = artifacts / "investigator.json"
    before = production_snapshot(repo)
    _record(trace, "investigator", 0, "stage_started")
    _invoke(trace, "investigator", 0, repo, run_root, investigation_path,
            _read_prompt(metadata, "investigator"), False)
    if production_snapshot(repo) != before:
        raise RuntimeError("investigator modified repository files")
    investigation_data = _load_object(investigation_path, "investigator")
    investigation = _dataclass_from_dict(InvestigationArtifact, investigation_data, "investigation")
    validate_investigation(investigation, repo)
    _record(trace, "investigator", 0, "artifact", output=json.dumps(investigation_data),
            evidence_id="investigation-artifact")
    _record(trace, "investigator", 0, "stage_completed")

    feedback: list[str] = []
    decision: VerificationDecision | None = None
    for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
        repair_path = artifacts / f"repair_agent-attempt-{attempt}.txt"
        _record(trace, "repair_agent", attempt, "attempt_started", output=json.dumps(feedback))
        repair_before = production_snapshot(repo)
        retry_context = "\n\nVerifier feedback for retry:\n" + json.dumps(feedback) if feedback else ""
        _invoke(trace, "repair_agent", attempt, repo, run_root, repair_path,
                _read_prompt(metadata, "repair_agent") + retry_context, True)
        repair_after = production_snapshot(repo)
        changed = _changed(repair_before, repair_after)
        forbidden = [name for name in changed if not (name == "app" or name.startswith("app/"))]
        if forbidden:
            raise RuntimeError(f"repair modified files outside app/: {forbidden}")
        _record(trace, "repair_agent", attempt, "attempt_completed", output=json.dumps(changed),
                evidence_id=f"app-diff-attempt-{attempt}")

        verifier_path = artifacts / f"verifier-attempt-{attempt}.json"
        verifier_prompt = _read_prompt(metadata, "verifier") + (
            f"\n\nThis is attempt {attempt}. Use only these deterministic verification evidence IDs: "
            f"visible-tests-attempt-{attempt} and contract-check-attempt-{attempt}."
        )
        verifier_before = production_snapshot(repo)
        _record(trace, "verifier", attempt, "stage_started")
        _invoke(trace, "verifier", attempt, repo, run_root, verifier_path, verifier_prompt, False,
                evidence_id=f"visible-tests-attempt-{attempt}")
        if production_snapshot(repo) != verifier_before:
            raise RuntimeError("verifier modified repository files")
        decision_data = _load_object(verifier_path, "verifier")
        decision = _dataclass_from_dict(VerificationDecision, decision_data, "verifier decision")
        decision.validate()
        allowed = {f"visible-tests-attempt-{attempt}", f"contract-check-attempt-{attempt}"}
        if not set(decision.verification_evidence_ids) <= allowed:
            raise RuntimeError("verifier referenced non-deterministic or unavailable evidence")
        _record(trace, "verifier", attempt, "artifact", output=json.dumps(decision_data),
                evidence_id=f"contract-check-attempt-{attempt}")
        _record(trace, "verifier", attempt, "decision", output=json.dumps(decision_data),
                decision="pass" if decision.passed else "fail",
                evidence_id=f"verifier-decision-attempt-{attempt}")
        if decision.passed:
            break
        for index, item in enumerate(_feedback_items(decision), 1):
            _record(trace, "verifier", attempt, "feedback", output=item,
                    evidence_id=f"verifier-feedback-attempt-{attempt}-{index}")
        feedback = _feedback_items(decision)

    assert decision is not None
    _finish_with_evidence_reporter(metadata, metadata_path, run_root, repo, trace, artifacts,
                                   investigation_path, verifier_path, attempt, decision)
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--resume-after-verifier", action="store_true")
    args = parser.parse_args()
    decision = (resume_after_verifier(args.run_id) if args.resume_after_verifier
                else run_final_workflow(args.run_id))
    print(json.dumps({"run_id": args.run_id, "verification_passed": decision.passed}, indent=2))


if __name__ == "__main__":
    main()

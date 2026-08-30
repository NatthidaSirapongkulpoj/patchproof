from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.evaluate_patchproof_final as evaluate_script
import scripts.prepare_patchproof_final as prepare_script
from patchproof.final.evidence import read_records
from patchproof.final.models import InvestigationArtifact, RunMetadata, VerificationDecision
from patchproof.final.workflow import FinalWorkflow
from scripts.summarize_patchproof_final import summarize


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "app").mkdir(parents=True)
    (repo / "app" / "main.py").write_text("value = 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_main.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
    return repo


def investigation(repo: Path) -> InvestigationArtifact:
    return InvestigationArtifact("wrong value", ["app/main.py"], ["value is two"], "change value")


def test_verifier_failure_can_trigger_exactly_one_retry(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    workflow = FinalWorkflow(RunMetadata("run", "PP-01"), repo, tmp_path / "trajectory.jsonl")
    attempts: list[int] = []

    def repair(path: Path, artifact: InvestigationArtifact, attempt: int, feedback: list[str]) -> None:
        attempts.append(attempt)
        (path / "app" / "main.py").write_text(f"value = {attempt}\n", encoding="utf-8")

    def verify(path: Path, artifact: InvestigationArtifact, attempt: int) -> VerificationDecision:
        return VerificationDecision(attempt == 2, ["checked"], ["app/main.py"], [f"test-{attempt}"], ["retry"])

    decision = workflow.run(investigation, repair, verify)
    assert decision.passed is True
    assert attempts == [1, 2]
    records = read_records(tmp_path / "trajectory.jsonl")
    assert len([item for item in records if item["event_type"] == "feedback"]) == 1


def test_third_repair_attempt_is_prohibited(tmp_path: Path) -> None:
    workflow = FinalWorkflow(RunMetadata("run", "PP-01"), make_repo(tmp_path), tmp_path / "trace")
    assert workflow.begin_repair_attempt() == 1
    assert workflow.begin_repair_attempt() == 2
    with pytest.raises(RuntimeError, match="third repair attempt"):
        workflow.begin_repair_attempt()


def test_hidden_evaluator_not_invoked_before_completion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id = "PP-01-patchproof-final-test"
    run_root = tmp_path / run_id
    repo = make_repo(run_root)
    metadata = {"run_id": run_id, "status": "prepared", "repo_path": str(repo)}
    (run_root / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(evaluate_script, "RUNS_ROOT", tmp_path)
    monkeypatch.setattr(evaluate_script.subprocess, "run", forbidden)
    with pytest.raises(ValueError, match="only after workflow completion"):
        evaluate_script.evaluate_final_run(run_id)
    assert called is False


def test_preparation_keeps_canonical_repository_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    canonical = make_repo(tmp_path / "canonical")
    isolated = make_repo(tmp_path / "isolated")
    issue = isolated.parent / "issue.md"
    issue.write_text("Fix value", encoding="utf-8")
    workspace = type("Workspace", (), {"root": isolated.parent, "repo": isolated, "issue_path": issue})()
    before = (canonical / "app" / "main.py").read_bytes()
    monkeypatch.setattr(prepare_script, "prepare_workspace", lambda *args: workspace)
    metadata = prepare_script.prepare_final_run("PP-01")
    assert (canonical / "app" / "main.py").read_bytes() == before
    assert metadata["benchmark_tag"] == "benchmark-v1"
    assert set(metadata["commands"]) == {"investigator", "repair_agent", "verifier", "evidence_reporter"}


def write_result(root: Path, name: str, case_id: str, success: bool, ready: bool) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{name}.json").write_text(json.dumps({
        "case_id": case_id, "run_id": name, "success": success, "gates": {"review_ready": ready}
    }), encoding="utf-8")


def test_summary_computes_vtsr_and_vrrr_and_missing_cases(tmp_path: Path) -> None:
    write_result(tmp_path, "one", "PP-01", True, True)
    write_result(tmp_path, "two", "PP-02", True, False)
    result = summarize(tmp_path)
    assert result["vtsr_percentage"] == 100.0
    assert result["vrrr_percentage"] == 50.0
    assert result["missing_cases"] == [f"PP-{number:02d}" for number in range(3, 13)]


def test_duplicate_official_final_results_are_rejected(tmp_path: Path) -> None:
    write_result(tmp_path, "one", "PP-01", True, True)
    write_result(tmp_path, "two", "PP-01", False, False)
    with pytest.raises(ValueError, match="duplicate official final results for PP-01"):
        summarize(tmp_path)

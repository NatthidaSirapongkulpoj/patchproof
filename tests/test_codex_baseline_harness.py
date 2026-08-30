from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.evaluate_codex_run as evaluate_script
import scripts.prepare_codex_baseline as prepare_script
from scripts.summarize_codex_baseline import summarize


def test_preparation_is_isolated_and_records_frozen_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    canonical = tmp_path / "canonical"
    repo = tmp_path / "run" / "repo"
    canonical.mkdir()
    repo.mkdir(parents=True)
    (canonical / "main.py").write_text("original\n", encoding="utf-8")
    (repo / "main.py").write_text("original\n", encoding="utf-8")
    issue = tmp_path / "run" / "issue.md"
    issue.write_text("Fix it.", encoding="utf-8")
    workspace = SimpleNamespace(root=repo.parent, repo=repo, issue_path=issue)
    monkeypatch.setattr(prepare_script, "prepare_workspace", lambda **_: workspace)

    metadata = prepare_script.prepare_codex_run("PP-01")
    (repo / "main.py").write_text("changed\n", encoding="utf-8")

    assert (canonical / "main.py").read_text(encoding="utf-8") == "original\n"
    assert metadata["benchmark_tag"] == "benchmark-v1"
    assert metadata["model"] == "gpt-5.6-sol"
    assert Path(metadata["prompt_path"]).parent == repo.parent
    assert Path(metadata["prompt_path"]).parent != repo


def test_evaluator_wrapper_resolves_prepared_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = tmp_path / "runs"
    run_id = "PP-02-codex-baseline-test"
    run_root = runs / run_id
    repo = run_root / "repo"
    repo.mkdir(parents=True)
    metadata = {
        "case_id": "PP-02",
        "run_id": run_id,
        "status": "prepared",
        "repo_path": str(repo),
        "benchmark_tag": "benchmark-v1",
        "baseline_prompt_version": "codex-baseline-v1",
        "execution_mode": "codex-cli",
        "model": "gpt-5.6-sol",
    }
    (run_root / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    evaluator_result = {
        "case_id": "PP-02",
        "success": True,
        "gates": {name: True for name in ("visible_tests", "hidden_acceptance", "patch_policy", "timeout")},
        "policy": {"changed_files": ["app/main.py"]},
    }
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        return SimpleNamespace(returncode=0, stdout=json.dumps(evaluator_result), stderr="")

    monkeypatch.setattr(evaluate_script, "RUNS_ROOT", runs)
    monkeypatch.setattr(evaluate_script, "EVIDENCE_ROOT", tmp_path / "evidence")
    monkeypatch.setattr(evaluate_script.subprocess, "run", fake_run)
    result = evaluate_script.evaluate_codex_run(run_id)

    assert str(repo.resolve()) in seen["command"]
    assert result["success"] is True
    updated = json.loads((run_root / "metadata.json").read_text(encoding="utf-8"))
    assert updated["status"] == "evaluated"
    assert updated["changed_files"] == ["app/main.py"]


def write_result(root: Path, name: str, case_id: str, success: bool) -> None:
    root.mkdir(parents=True, exist_ok=True)
    data = {
        "case_id": case_id,
        "run_id": name,
        "success": success,
        "gates": {gate: success for gate in ("visible_tests", "hidden_acceptance", "patch_policy", "timeout")},
    }
    (root / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")


def test_summarizer_computes_vtsr_and_reports_missing(tmp_path: Path) -> None:
    write_result(tmp_path, "one", "PP-01", True)
    write_result(tmp_path, "two", "PP-02", False)
    result = summarize(tmp_path)
    assert result["evaluated_case_count"] == 2
    assert result["successful_case_count"] == 1
    assert result["failed_case_count"] == 1
    assert result["vtsr_percentage"] == 50.0
    assert result["missing_cases"] == [f"PP-{number:02d}" for number in range(3, 13)]


def test_summarizer_rejects_duplicate_case_results(tmp_path: Path) -> None:
    write_result(tmp_path, "one", "PP-01", True)
    write_result(tmp_path, "two", "PP-01", False)
    with pytest.raises(ValueError, match="duplicate official results for PP-01"):
        summarize(tmp_path)

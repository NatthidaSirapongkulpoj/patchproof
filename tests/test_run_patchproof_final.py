from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.run_patchproof_final as runner
from patchproof.final.evidence import evidence_integrity_pass, read_records


def make_run(tmp_path: Path, run_id: str = "PP-01-patchproof-final-test") -> Path:
    root = tmp_path / run_id
    repo = root / "repo"
    artifacts = root / "artifacts"
    prompts = root / "prompts"
    (repo / "app").mkdir(parents=True)
    (repo / "tests").mkdir()
    artifacts.mkdir()
    prompts.mkdir()
    (repo / "app" / "main.py").write_text("value = 1\n", encoding="utf-8")
    (repo / "tests" / "test_main.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
    prompt_paths = {}
    for role in ("investigator", "repair_agent", "verifier", "evidence_reporter"):
        path = prompts / f"{role}.md"
        path.write_text(role, encoding="utf-8")
        prompt_paths[role] = str(path)
    metadata = {
        "run_id": run_id,
        "case_id": "PP-01",
        "status": "prepared",
        "workflow_version": "patchproof-final-v2",
        "repo_path": str(repo),
        "artifact_root": str(artifacts),
        "trace_path": str(root / "trajectory.jsonl"),
        "prompts": prompt_paths,
    }
    (root / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return root


def fake_codex(root: Path, outcomes: list[bool], *, mutation: tuple[str, str] | None = None,
               malformed_role: str | None = None, fail_role: str | None = None):
    counts = {"repair_agent": 0, "verifier": 0}

    def run(command, **kwargs):
        prompt = kwargs["input"]
        artifact = Path(command[command.index("--output-last-message") + 1])
        role = next(name for name in ("investigator", "repair_agent", "verifier", "evidence_reporter")
                    if prompt.startswith(name))
        if role == fail_role:
            return SimpleNamespace(returncode=7, stdout="", stderr="codex failed")
        if mutation and role == mutation[0]:
            target = root / "repo" / mutation[1]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("mutated\n", encoding="utf-8")
        if role == "investigator":
            value = {"root_cause": "wrong value", "relevant_files": ["app/main.py"],
                     "behavioral_contracts": ["value changes"], "proposed_repair": "change it",
                     "uncertainties": []}
        elif role == "repair_agent":
            counts[role] += 1
            (root / "repo" / "app" / "main.py").write_text(
                f"value = {counts[role] + 1}\n", encoding="utf-8")
            value = "repair complete"
        elif role == "verifier":
            counts[role] += 1
            attempt = counts[role]
            passed = outcomes[attempt - 1]
            value = {"passed": passed, "findings": ["checked"], "inspected_files": ["app/main.py"],
                     "verification_evidence_ids": [f"visible-tests-attempt-{attempt}"],
                     "retry_feedback": [] if passed else ["fix the value"]}
        else:
            attempt = counts["verifier"]
            value = {"root_cause": "wrong value", "changed_files": ["app/main.py"],
                     "behavior_fixed": "value fixed",
                     "verification_performed": [{"check": "tests", "evidence_id": f"visible-tests-attempt-{attempt}"}],
                     "verification_results": [{"result": "verifier", "evidence_id": f"verifier-decision-attempt-{attempt}"}],
                     "remaining_risk": "hidden checks pending", "human_review_action": "review the diff",
                     "ready_for_human_review": False}
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("not json" if role == malformed_role else
                            (value if isinstance(value, str) else json.dumps(value)), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    return run, counts


def setup_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcomes: list[bool], **kwargs):
    root = make_run(tmp_path)
    fake, counts = fake_codex(root, outcomes, **kwargs)
    monkeypatch.setattr(runner, "RUNS_ROOT", tmp_path)
    monkeypatch.setattr(runner, "resolve_codex_executable", lambda: "resolved-codex")
    monkeypatch.setattr(runner.subprocess, "run", fake)
    return root, counts


def test_windows_prefers_codex_cmd(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(runner.os, "name", "nt")
    monkeypatch.setattr(runner.shutil, "which", lambda name: calls.append(name) or {
        "codex.cmd": r"C:\npm\codex.cmd", "codex": r"C:\npm\codex"
    }.get(name))
    assert runner.resolve_codex_executable() == r"C:\npm\codex.cmd"
    assert calls == ["codex.cmd"]


def test_windows_falls_back_to_codex(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(runner.os, "name", "nt")
    monkeypatch.setattr(runner.shutil, "which", lambda name: calls.append(name) or (
        r"C:\npm\codex" if name == "codex" else None
    ))
    assert runner.resolve_codex_executable() == r"C:\npm\codex"
    assert calls == ["codex.cmd", "codex"]


def test_non_windows_resolves_codex(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(runner.os, "name", "posix")
    monkeypatch.setattr(runner.shutil, "which", lambda name: calls.append(name) or "/usr/bin/codex")
    assert runner.resolve_codex_executable() == "/usr/bin/codex"
    assert calls == ["codex"]


def test_missing_codex_fails_clearly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner.os, "name", "nt")
    monkeypatch.setattr(runner.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="Codex executable not found on PATH"):
        runner.resolve_codex_executable()


def test_command_uses_resolved_executable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "resolve_codex_executable", lambda: r"C:\npm\codex.cmd")
    command = runner._command(tmp_path, tmp_path / "run", tmp_path / "artifact", False)
    assert command[0] == r"C:\npm\codex.cmd"


def test_invoke_sends_unicode_prompt_as_explicit_utf8_and_records_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = tmp_path / "trajectory.jsonl"
    artifact = tmp_path / "artifact.txt"
    prompt = "Investigate the em dash — and non-ASCII text: café, ไทย"
    observed = {}

    def accept_unicode(command, **kwargs):
        observed.update(kwargs)
        assert kwargs["input"] == prompt
        assert prompt.encode(kwargs["encoding"], kwargs["errors"]).decode("utf-8") == prompt
        artifact.write_text("complete", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="résultat ไทย", stderr="คำเตือน")

    monkeypatch.setattr(runner, "resolve_codex_executable", lambda: r"C:\npm\codex.cmd")
    monkeypatch.setattr(runner.subprocess, "run", accept_unicode)
    runner._invoke(trace, "investigator", 0, tmp_path, tmp_path, artifact, prompt, False)

    assert observed["text"] is True
    assert observed["encoding"] == "utf-8"
    assert observed["errors"] == "strict"
    assert observed["shell"] is False
    result = next(item for item in read_records(trace) if item["event_type"] == "command_result")
    output = json.loads(result["output"])
    assert isinstance(output["stdout"], str) and output["stdout"] == "résultat ไทย"
    assert isinstance(output["stderr"], str) and output["stderr"] == "คำเตือน"


def test_nonzero_unicode_invocation_records_result_and_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = tmp_path / "trajectory.jsonl"
    artifact = tmp_path / "artifact.txt"

    def fail(command, **kwargs):
        assert kwargs["encoding"] == "utf-8"
        return SimpleNamespace(returncode=7, stdout="partial — output", stderr="échec ไทย")

    monkeypatch.setattr(runner, "resolve_codex_executable", lambda: r"C:\npm\codex.cmd")
    monkeypatch.setattr(runner.subprocess, "run", fail)
    with pytest.raises(RuntimeError, match="subprocess exited 7"):
        runner._invoke(trace, "investigator", 0, tmp_path, tmp_path, artifact,
                       "Unicode — café ไทย", False)

    result = next(item for item in read_records(trace) if item["event_type"] == "command_result")
    output = json.loads(result["output"])
    assert result["exit_code"] == 7
    assert output == {"stdout": "partial — output", "stderr": "échec ไทย"}
    assert all(isinstance(value, str) for value in output.values())


def test_process_creation_failure_is_recorded_without_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = make_run(tmp_path)
    monkeypatch.setattr(runner, "RUNS_ROOT", tmp_path)
    monkeypatch.setattr(runner, "resolve_codex_executable", lambda: r"C:\npm\codex.cmd")

    def fail_creation(command, **kwargs):
        raise FileNotFoundError(2, "The system cannot find the file specified")

    monkeypatch.setattr(runner.subprocess, "run", fail_creation)
    with pytest.raises(RuntimeError, match="subprocess could not be created"):
        runner.run_final_workflow(root.name)

    records = read_records(root / "trajectory.jsonl")
    result = next(item for item in records if item["event_type"] == "command_result")
    assert result["command"].startswith(r"C:\npm\codex.cmd")
    assert "The system cannot find the file specified" in result["output"]
    assert result["exit_code"] == -1
    assert not any(item["event_type"] == "workflow_completed" for item in records)
    assert json.loads((root / "metadata.json").read_text())["status"] == "prepared"


def test_one_command_completes_trace_without_hidden_evaluator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, counts = setup_runner(tmp_path, monkeypatch, [True])
    decision = runner.run_final_workflow(root.name)
    records = read_records(root / "trajectory.jsonl")
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    assert decision.passed and counts == {"repair_agent": 1, "verifier": 1}
    assert metadata["status"] == "workflow_completed"
    assert any(item["event_type"] == "workflow_completed" for item in records)
    assert any(item["event_type"] == "human_review_checkpoint" for item in records)
    assert all("evaluator" not in (item["command"] or "") for item in records)


def test_failed_verifier_feedback_precedes_single_retry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, counts = setup_runner(tmp_path, monkeypatch, [False, True])
    runner.run_final_workflow(root.name)
    records = read_records(root / "trajectory.jsonl")
    feedback = next(i for i, item in enumerate(records) if item["event_type"] == "feedback")
    retry = next(i for i, item in enumerate(records)
                 if item["event_type"] == "attempt_started" and item["attempt"] == 2)
    assert feedback < retry
    assert counts == {"repair_agent": 2, "verifier": 2}
    assert not any(item["attempt"] == 3 for item in records)


@pytest.mark.parametrize("role", ["investigator", "verifier"])
def test_read_only_role_modification_is_rejected(role: str, tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = setup_runner(tmp_path, monkeypatch, [True], mutation=(role, "app/main.py"))
    with pytest.raises(RuntimeError, match=f"{role.replace('_', ' ')} modified repository"):
        runner.run_final_workflow(root.name)
    assert json.loads((root / "metadata.json").read_text())["status"] == "prepared"


def test_repair_outside_app_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = setup_runner(tmp_path, monkeypatch, [True], mutation=("repair_agent", "tests/test_main.py"))
    with pytest.raises(RuntimeError, match="outside app"):
        runner.run_final_workflow(root.name)


@pytest.mark.parametrize("failure", ["nonzero", "malformed"])
def test_subprocess_or_json_failure_does_not_complete(failure: str, tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    kwargs = {"fail_role": "investigator"} if failure == "nonzero" else {"malformed_role": "investigator"}
    root, _ = setup_runner(tmp_path, monkeypatch, [True], **kwargs)
    with pytest.raises(RuntimeError):
        runner.run_final_workflow(root.name)
    assert json.loads((root / "metadata.json").read_text())["status"] == "prepared"


def test_missing_review_evidence_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = setup_runner(tmp_path, monkeypatch, [True])
    original = runner.evidence_integrity_pass
    monkeypatch.setattr(runner, "evidence_integrity_pass", lambda artifact, records: False)
    with pytest.raises(RuntimeError, match="missing trajectory evidence"):
        runner.run_final_workflow(root.name)
    assert original({"verification_performed": [{"evidence_id": "missing"}],
                     "verification_results": []}, read_records(root / "trajectory.jsonl")) is False


def test_review_references_resolve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = setup_runner(tmp_path, monkeypatch, [False, False])
    decision = runner.run_final_workflow(root.name)
    review = json.loads((root / "artifacts" / "evidence_reporter.json").read_text())
    assert decision.passed is False
    assert evidence_integrity_pass(review, read_records(root / "trajectory.jsonl"))

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Callable

from .evidence import append_record
from .investigator import production_snapshot, validate_investigation
from .models import (
    InvestigationArtifact,
    RunMetadata,
    TrajectoryRecord,
    VerificationDecision,
    utc_now,
)


MAX_REPAIR_ATTEMPTS = 2


class FinalWorkflow:
    """Orchestrates investigator, repair and independent verifier callbacks."""

    def __init__(self, metadata: RunMetadata, repo: Path, trace_path: Path) -> None:
        self.metadata = metadata
        self.repo = repo.resolve()
        self.trace_path = trace_path
        self.attempts = 0
        self.completed = False

    def _record(self, role: str, attempt: int, event_type: str, **values: object) -> None:
        append_record(
            self.trace_path,
            TrajectoryRecord(
                timestamp=utc_now(), role=role, attempt=attempt, event_type=event_type, **values
            ),
        )

    def run(
        self,
        investigate: Callable[[Path], InvestigationArtifact],
        repair: Callable[[Path, InvestigationArtifact, int, list[str]], None],
        verify: Callable[[Path, InvestigationArtifact, int], VerificationDecision],
    ) -> VerificationDecision:
        before = production_snapshot(self.repo)
        investigation = investigate(self.repo)
        if production_snapshot(self.repo) != before:
            raise RuntimeError("investigator modified production files")
        validate_investigation(investigation, self.repo)
        self._record("investigator", 0, "artifact", output=str(investigation.to_dict()), evidence_id="investigation-1")

        feedback: list[str] = []
        decision: VerificationDecision | None = None
        for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
            self.attempts = attempt
            self._record("repair_agent", attempt, "attempt_started", output=str(feedback))
            repair_before = production_snapshot(self.repo)
            repair(self.repo, investigation, attempt, feedback)
            repair_after = production_snapshot(self.repo)
            changed = set(repair_before) | set(repair_after)
            forbidden = sorted(
                name for name in changed
                if repair_before.get(name) != repair_after.get(name)
                and not (name == "app" or name.startswith("app/"))
            )
            if forbidden:
                raise RuntimeError(f"repair modified files outside app/: {forbidden}")
            self._record("repair_agent", attempt, "attempt_completed", evidence_id=f"repair-{attempt}")
            verifier_before = production_snapshot(self.repo)
            decision = verify(self.repo, investigation, attempt)
            if production_snapshot(self.repo) != verifier_before:
                raise RuntimeError("verifier modified repository files")
            decision.validate()
            self._record(
                "verifier", attempt, "decision",
                output=str(decision.to_dict()),
                decision="pass" if decision.passed else "fail",
                evidence_id=f"verifier-{attempt}",
            )
            if decision.passed:
                break
            for index, item in enumerate(decision.retry_feedback, 1):
                self._record("verifier", attempt, "feedback", output=item, evidence_id=f"feedback-{attempt}-{index}")
            feedback = list(decision.retry_feedback or decision.findings)

        assert decision is not None
        self.completed = True
        self.metadata = replace(self.metadata, status="workflow_completed")
        metadata_path = self.trace_path.parent / "metadata.json"
        if metadata_path.is_file():
            persisted = json.loads(metadata_path.read_text(encoding="utf-8"))
            persisted["status"] = "workflow_completed"
            metadata_path.write_text(json.dumps(persisted, indent=2) + "\n", encoding="utf-8")
        return decision

    def begin_repair_attempt(self) -> int:
        if self.attempts >= MAX_REPAIR_ATTEMPTS:
            raise RuntimeError("third repair attempt is prohibited")
        self.attempts += 1
        return self.attempts

    def assert_hidden_evaluation_allowed(self) -> None:
        if not self.completed:
            raise RuntimeError("hidden evaluator cannot run before workflow completion")

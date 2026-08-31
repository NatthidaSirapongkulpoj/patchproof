from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import re


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    case_id: str
    benchmark_tag: str = "benchmark-v1"
    execution_mode: str = "codex-cli"
    model: str = "gpt-5.6-sol"
    workflow_version: str = "patchproof-final-v2"
    created_at: str = field(default_factory=utc_now)
    status: str = "prepared"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrajectoryRecord:
    timestamp: str
    role: str
    attempt: int
    event_type: str
    command: str | None = None
    output: str | None = None
    exit_code: int | None = None
    decision: str | None = None
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InvestigationArtifact:
    root_cause: str
    relevant_files: list[str]
    behavioral_contracts: list[str]
    proposed_repair: str
    uncertainties: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.root_cause.strip() or not self.relevant_files:
            raise ValueError("investigation must identify a root cause and relevant files")
        if not self.behavioral_contracts or not self.proposed_repair.strip():
            raise ValueError("investigation must identify contracts and a proposed repair")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationDecision:
    passed: bool
    findings: list[str]
    inspected_files: list[str]
    verification_evidence_ids: list[str]
    retry_feedback: list[str] | str = field(default_factory=list)

    def validate(self) -> None:
        if not isinstance(self.passed, bool):
            raise ValueError("verifier passed must be a boolean")
        if not isinstance(self.findings, list) or any(
            not isinstance(item, str) for item in self.findings
        ):
            raise ValueError("verifier findings must be a list of strings")
        if not isinstance(self.inspected_files, list) or any(
            not isinstance(item, str) or not item.strip() for item in self.inspected_files
        ):
            raise ValueError("verifier inspected_files must contain non-empty strings")
        if not isinstance(self.verification_evidence_ids, list) or any(
            not isinstance(item, str)
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item)
            for item in self.verification_evidence_ids
        ):
            raise ValueError("verifier evidence IDs are malformed")
        if not isinstance(self.retry_feedback, (list, str)) or (
            isinstance(self.retry_feedback, list)
            and any(not isinstance(item, str) for item in self.retry_feedback)
        ):
            raise ValueError("verifier retry_feedback must be text or a list of strings")
        findings_present = any(item.strip() for item in self.findings)
        feedback_items = (
            [self.retry_feedback] if isinstance(self.retry_feedback, str) else self.retry_feedback
        )
        feedback_present = any(item.strip() for item in feedback_items)
        if self.passed and not self.verification_evidence_ids:
            raise ValueError("verifier pass must reference verification evidence")
        if not self.passed and not (findings_present or feedback_present):
            raise ValueError("verifier failure must contain actionable findings or retry feedback")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewArtifact:
    root_cause: str
    changed_files: list[str]
    behavior_fixed: str
    verification_performed: list[dict[str, str]]
    verification_results: list[dict[str, str]]
    remaining_risk: str
    human_review_action: str
    ready_for_human_review: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    case_id: str
    benchmark_tag: str = "benchmark-v1"
    execution_mode: str = "codex-cli"
    model: str = "gpt-5.6-sol"
    workflow_version: str = "patchproof-final-v1"
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
    retry_feedback: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.findings:
            raise ValueError("verifier decision must contain findings")
        if self.passed and not self.verification_evidence_ids:
            raise ValueError("verifier pass must reference verification evidence")

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

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import ReviewArtifact, TrajectoryRecord


REQUIRED_REVIEW_FIELDS = (
    "root_cause",
    "changed_files",
    "behavior_fixed",
    "verification_performed",
    "verification_results",
    "remaining_risk",
    "human_review_action",
)


def append_record(path: Path, record: TrajectoryRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def read_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def recorded_evidence_ids(records: Iterable[dict]) -> set[str]:
    return {str(item["evidence_id"]) for item in records if item.get("evidence_id")}


def verification_claim_ids(artifact: dict) -> set[str]:
    claims = list(artifact.get("verification_performed") or []) + list(
        artifact.get("verification_results") or []
    )
    return {str(claim.get("evidence_id", "")) for claim in claims}


def evidence_integrity_pass(artifact: dict, records: Iterable[dict]) -> bool:
    references = verification_claim_ids(artifact)
    return bool(references) and "" not in references and references <= recorded_evidence_ids(records)


def review_artifact_complete(artifact: dict) -> bool:
    return all(bool(artifact.get(field)) for field in REQUIRED_REVIEW_FIELDS)


def write_review_artifact(path: Path, artifact: ReviewArtifact, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**metadata, **artifact.to_dict()}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

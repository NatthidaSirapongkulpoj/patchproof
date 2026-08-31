from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import InvestigationArtifact


def normalize_investigation(value: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical investigator schema without mutating the raw value."""
    relevant_files = value.get("relevant_files")
    if not isinstance(relevant_files, list):
        raise ValueError("investigation relevant_files must be a list")
    canonical_files: list[str] = []
    for entry in relevant_files:
        if isinstance(entry, str):
            name = entry
        elif isinstance(entry, dict):
            if "path" not in entry:
                raise ValueError("relevant file object is missing path")
            unknown = set(entry) - {"path", "relevance"}
            if unknown:
                raise ValueError(f"unsupported relevant file object fields: {sorted(unknown)}")
            if "relevance" in entry and not isinstance(entry["relevance"], str):
                raise ValueError("relevant file relevance must be a string")
            name = entry["path"]
        else:
            raise ValueError("unsupported relevant file entry type")
        if not isinstance(name, str):
            raise ValueError("relevant file path must be a string")
        if not name.strip():
            raise ValueError("relevant file path must be non-empty")
        canonical_files.append(name)
    canonical = dict(value)
    canonical["relevant_files"] = canonical_files
    return canonical


def validate_investigation(artifact: InvestigationArtifact, repo: Path) -> None:
    """Validate an investigator result without permitting repository mutation."""
    artifact.validate()
    for name in artifact.relevant_files:
        path = Path(name)
        try:
            resolved = (repo / path).resolve()
            resolved.relative_to(repo.resolve())
        except (OSError, ValueError):
            raise ValueError(f"unsafe relevant file path: {name}") from None
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe relevant file path: {name}")
        if not resolved.is_file():
            raise ValueError(f"relevant file does not exist: {name}")


def production_snapshot(repo: Path) -> dict[str, bytes]:
    """Capture repository bytes so a harness can enforce read-only stages."""
    return {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in sorted(repo.rglob("*"))
        if path.is_file()
    }

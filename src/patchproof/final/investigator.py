from __future__ import annotations

from pathlib import Path

from .models import InvestigationArtifact


def validate_investigation(artifact: InvestigationArtifact, repo: Path) -> None:
    """Validate an investigator result without permitting repository mutation."""
    artifact.validate()
    for name in artifact.relevant_files:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe relevant file path: {name}")
        if not (repo / path).is_file():
            raise ValueError(f"relevant file does not exist: {name}")


def production_snapshot(repo: Path) -> dict[str, bytes]:
    """Capture repository bytes so a harness can enforce read-only stages."""
    return {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in sorted(repo.rglob("*"))
        if path.is_file()
    }

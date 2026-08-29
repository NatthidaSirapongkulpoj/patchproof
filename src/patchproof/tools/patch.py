from __future__ import annotations

from pathlib import Path

from patchproof.models import ToolResult


def _resolve_allowed_app_path(
    repository_root: Path,
    relative_path: str,
) -> Path:
    repository_root = repository_root.resolve()
    app_root = (repository_root / "app").resolve()
    target = (repository_root / relative_path).resolve()

    if target != app_root and app_root not in target.parents:
        raise ValueError(
            "Writes are allowed only inside app/"
        )

    return target


def write_file(
    repository_root: Path,
    relative_path: str,
    content: str,
) -> ToolResult:
    try:
        target = _resolve_allowed_app_path(
            repository_root,
            relative_path,
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

        return ToolResult(
            ok=True,
            output=f"Wrote {relative_path}",
        )

    except Exception as exc:
        return ToolResult(
            ok=False,
            output=f"{type(exc).__name__}: {exc}",
        )

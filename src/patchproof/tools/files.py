from __future__ import annotations

from pathlib import Path

from patchproof.models import ToolResult


def _resolve_inside(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    target = (root / relative_path).resolve()

    if target != root and root not in target.parents:
        raise ValueError("Path escapes workspace")

    return target


def list_files(
    root: Path,
    relative_path: str = ".",
) -> ToolResult:
    try:
        target = _resolve_inside(root, relative_path)

        if not target.exists():
            return ToolResult(
                ok=False,
                output=f"Path not found: {relative_path}",
            )

        if target.is_file():
            return ToolResult(
                ok=True,
                output=relative_path,
            )

        files = []

        for path in sorted(target.rglob("*")):
            if not path.is_file():
                continue

            if "__pycache__" in path.parts:
                continue

            files.append(
                path.relative_to(root).as_posix()
            )

        return ToolResult(
            ok=True,
            output="\n".join(files),
        )

    except Exception as exc:
        return ToolResult(
            ok=False,
            output=f"{type(exc).__name__}: {exc}",
        )


def read_file(
    root: Path,
    relative_path: str,
) -> ToolResult:
    try:
        target = _resolve_inside(root, relative_path)

        if not target.is_file():
            return ToolResult(
                ok=False,
                output=f"File not found: {relative_path}",
            )

        return ToolResult(
            ok=True,
            output=target.read_text(
                encoding="utf-8",
            ),
        )

    except Exception as exc:
        return ToolResult(
            ok=False,
            output=f"{type(exc).__name__}: {exc}",
        )

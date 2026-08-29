from __future__ import annotations

from pathlib import Path

from patchproof.models import ToolResult


def search_text(
    root: Path,
    query: str,
) -> ToolResult:
    matches: list[str] = []

    try:
        root = root.resolve()

        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue

            if "__pycache__" in path.parts:
                continue

            try:
                text = path.read_text(
                    encoding="utf-8",
                )
            except UnicodeDecodeError:
                continue

            for line_number, line in enumerate(
                text.splitlines(),
                start=1,
            ):
                if query.lower() in line.lower():
                    relative = path.relative_to(root)

                    matches.append(
                        f"{relative.as_posix()}:{line_number}: {line}"
                    )

        return ToolResult(
            ok=True,
            output="\n".join(matches),
            metadata={
                "match_count": len(matches),
            },
        )

    except Exception as exc:
        return ToolResult(
            ok=False,
            output=f"{type(exc).__name__}: {exc}",
        )

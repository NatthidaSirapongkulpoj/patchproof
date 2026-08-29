from __future__ import annotations

import hashlib
from pathlib import Path


IGNORED_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".coverage",
}

IGNORED_SUFFIXES = {
    ".pyc",
    ".pyo",
}


def should_ignore(path: Path) -> bool:
    if any(part in IGNORED_NAMES for part in path.parts):
        return True

    if path.suffix in IGNORED_SUFFIXES:
        return True

    return False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def snapshot_tree(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}

    if not root.exists():
        return result

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        relative = path.relative_to(root)

        if should_ignore(relative):
            continue

        result[relative.as_posix()] = sha256_file(path)

    return result


def check_patch_policy(
    canonical_repo: Path,
    workspace_repo: Path,
) -> dict:
    """
    Compare a repaired workspace with the pristine benchmark repository.

    Current benchmark policy:
    - production changes are allowed only under app/
    - tests must not be changed
    - arbitrary new files outside app/ are forbidden
    """

    before = snapshot_tree(canonical_repo)
    after = snapshot_tree(workspace_repo)

    all_paths = sorted(set(before) | set(after))

    changed_files: list[str] = []
    forbidden_files: list[str] = []

    for relative in all_paths:
        if before.get(relative) == after.get(relative):
            continue

        changed_files.append(relative)

        allowed = (
            relative == "app"
            or relative.startswith("app/")
        )

        if not allowed:
            forbidden_files.append(relative)

    return {
        "passed": len(forbidden_files) == 0,
        "changed_files": changed_files,
        "forbidden_files": forbidden_files,
    }

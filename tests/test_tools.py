from pathlib import Path

from patchproof.tools.files import (
    list_files,
    read_file,
)
from patchproof.tools.patch import write_file
from patchproof.tools.search import search_text
from patchproof.tools.shell import run_command


def test_file_tools(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    app = repo / "app"

    app.mkdir(parents=True)

    (app / "main.py").write_text(
        "value = 123\n",
        encoding="utf-8",
    )

    listing = list_files(repo)
    assert listing.ok is True
    assert "app/main.py" in listing.output

    content = read_file(
        repo,
        "app/main.py",
    )

    assert content.ok is True
    assert "value = 123" in content.output


def test_search_text(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    app = repo / "app"

    app.mkdir(parents=True)

    (app / "main.py").write_text(
        "raise NotFoundError('missing')\n",
        encoding="utf-8",
    )

    result = search_text(
        repo,
        "NotFoundError",
    )

    assert result.ok is True
    assert result.metadata["match_count"] == 1


def test_write_file_allows_app_only(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"

    (repo / "app").mkdir(
        parents=True,
    )

    allowed = write_file(
        repo,
        "app/main.py",
        "x = 1\n",
    )

    blocked = write_file(
        repo,
        "tests/test_main.py",
        "assert False\n",
    )

    assert allowed.ok is True
    assert blocked.ok is False


def test_shell_rejects_unapproved_command(
    tmp_path: Path,
) -> None:
    result = run_command(
        tmp_path,
        "git status",
    )

    assert result.ok is False
    assert "rejected" in result.output.lower()

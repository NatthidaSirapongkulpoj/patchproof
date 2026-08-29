from pathlib import Path

from patchproof.tools.files import (
    list_files,
    read_file,
)
from patchproof.tools.patch import (
    replace_text,
    write_file,
)
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


def test_replace_text_changes_exactly_one_match(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    app = repo / "app"
    app.mkdir(parents=True)

    target = app / "main.py"
    target.write_text(
        "quantity: int\n",
        encoding="utf-8",
    )

    result = replace_text(
        repo,
        "app/main.py",
        "quantity: int",
        "quantity: int = Field(ge=1)",
    )

    assert result.ok is True
    assert target.read_text(
        encoding="utf-8"
    ) == "quantity: int = Field(ge=1)\n"


def test_replace_text_rejects_ambiguous_match(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    app = repo / "app"
    app.mkdir(parents=True)

    target = app / "main.py"
    target.write_text(
        "value = 1\nvalue = 1\n",
        encoding="utf-8",
    )

    result = replace_text(
        repo,
        "app/main.py",
        "value = 1",
        "value = 2",
    )

    assert result.ok is False
    assert "ambiguous" in result.output.lower()


def test_replace_text_blocks_outside_app(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    tests = repo / "tests"
    tests.mkdir(parents=True)

    target = tests / "test_main.py"
    target.write_text(
        "assert True\n",
        encoding="utf-8",
    )

    result = replace_text(
        repo,
        "tests/test_main.py",
        "True",
        "False",
    )

    assert result.ok is False
    assert target.read_text(
        encoding="utf-8"
    ) == "assert True\n"


def test_shell_rejects_unapproved_command(
    tmp_path: Path,
) -> None:
    result = run_command(
        tmp_path,
        "git status",
    )

    assert result.ok is False
    assert "rejected" in result.output.lower()

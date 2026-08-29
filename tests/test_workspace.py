from patchproof.workspace import (
    BENCHMARK_CASES,
    prepare_workspace,
)


def test_workspace_is_copy_of_canonical_case() -> None:
    workspace = prepare_workspace(
        case_id="PP-01",
        run_id="test-pp01",
    )

    canonical = (
        BENCHMARK_CASES
        / "PP-01"
        / "repo"
        / "app"
        / "main.py"
    )

    copied = (
        workspace.repo
        / "app"
        / "main.py"
    )

    assert copied.exists()
    assert copied.read_text() == canonical.read_text()


def test_workspace_changes_do_not_modify_canonical() -> None:
    workspace = prepare_workspace(
        case_id="PP-01",
        run_id="test-isolation",
    )

    canonical = (
        BENCHMARK_CASES
        / "PP-01"
        / "repo"
        / "app"
        / "main.py"
    )

    original = canonical.read_text()

    copied = (
        workspace.repo
        / "app"
        / "main.py"
    )

    copied.write_text(
        copied.read_text()
        + "\n# workspace-only change\n"
    )

    assert canonical.read_text() == original

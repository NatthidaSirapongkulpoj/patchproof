from pathlib import Path
import shutil

from benchmark.evaluator.policy import check_patch_policy


def test_policy_allows_app_changes(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    workspace = tmp_path / "workspace"

    (canonical / "app").mkdir(parents=True)
    (workspace / "app").mkdir(parents=True)

    (canonical / "app" / "main.py").write_text("x = 1\n")
    shutil.copytree(canonical, workspace, dirs_exist_ok=True)

    (workspace / "app" / "main.py").write_text("x = 2\n")

    result = check_patch_policy(canonical, workspace)

    assert result["passed"] is True
    assert result["forbidden_files"] == []


def test_policy_blocks_test_changes(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    workspace = tmp_path / "workspace"

    (canonical / "app").mkdir(parents=True)
    (canonical / "tests").mkdir(parents=True)

    (canonical / "app" / "main.py").write_text("x = 1\n")
    (canonical / "tests" / "test_main.py").write_text(
        "def test_ok(): pass\n"
    )

    shutil.copytree(canonical, workspace)

    (workspace / "tests" / "test_main.py").write_text(
        "def test_ok(): assert False\n"
    )

    result = check_patch_policy(canonical, workspace)

    assert result["passed"] is False
    assert "tests/test_main.py" in result["forbidden_files"]

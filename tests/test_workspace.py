"""Tests for harness.workspace (PLAN step 3.4)."""
import pathlib
from unittest.mock import MagicMock, patch

import pytest

from harness.workspace import provision


def _mock_clone_success(cmd, **kwargs):
    m = MagicMock()
    m.returncode = 0
    m.stderr = ""
    # Actually create the destination directory so copytree works
    dest = pathlib.Path(cmd[-1])
    dest.mkdir(parents=True, exist_ok=True)
    return m


def _mock_clone_failure(cmd, **kwargs):
    m = MagicMock()
    m.returncode = 1
    m.stderr = "fatal: repository not found"
    return m


def test_provision_creates_subdirectory(tmp_path):
    harness_root = tmp_path / "harness"
    harness_root.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    with patch("harness.workspace.subprocess.run", side_effect=_mock_clone_success):
        clone_path = provision(str(work_dir), "https://github.com/owner/repo", str(harness_root))

    assert clone_path.exists()
    assert clone_path.is_dir()
    assert str(work_dir) in str(clone_path)


def test_provision_raises_on_clone_failure(tmp_path):
    harness_root = tmp_path / "harness"
    harness_root.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    with patch("harness.workspace.subprocess.run", side_effect=_mock_clone_failure):
        with pytest.raises(RuntimeError, match="git clone failed"):
            provision(str(work_dir), "https://github.com/owner/repo", str(harness_root))


def test_provision_copies_github_dir(tmp_path):
    harness_root = tmp_path / "harness"
    github_dir = harness_root / ".github"
    github_dir.mkdir(parents=True)
    (github_dir / "config.yml").write_text("key: value")

    work_dir = tmp_path / "work"
    work_dir.mkdir()

    with patch("harness.workspace.subprocess.run", side_effect=_mock_clone_success):
        clone_path = provision(str(work_dir), "https://github.com/owner/repo", str(harness_root))

    assert (clone_path / ".github" / "config.yml").exists()


def test_provision_does_not_overwrite_existing_github_file(tmp_path):
    harness_root = tmp_path / "harness"
    github_dir = harness_root / ".github"
    github_dir.mkdir(parents=True)
    (github_dir / "config.yml").write_text("harness content")

    work_dir = tmp_path / "work"
    work_dir.mkdir()

    def mock_clone_with_existing(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stderr = ""
        dest = pathlib.Path(cmd[-1])
        dest_github = dest / ".github"
        dest_github.mkdir(parents=True, exist_ok=True)
        (dest_github / "config.yml").write_text("existing content")
        return m

    with patch("harness.workspace.subprocess.run", side_effect=mock_clone_with_existing):
        clone_path = provision(str(work_dir), "https://github.com/owner/repo", str(harness_root))

    # Existing file must not be overwritten
    assert (clone_path / ".github" / "config.yml").read_text() == "existing content"

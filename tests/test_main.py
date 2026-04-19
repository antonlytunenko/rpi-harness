"""Tests for main.py run-loop changes (PLAN steps 3.1 and 3.2)."""
from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, call, patch

import pytest

import main as m


# ---------------------------------------------------------------------------
# Step 3.1 — agent-ready detection split
# ---------------------------------------------------------------------------


def test_find_labeled_items_called_with_issue_labels_and_pr_labels(tmp_path):
    """find_labeled_items must be called once with ISSUE_LABELS and once with PR_LABELS."""
    repos_file = tmp_path / "repos.txt"
    repos_file.write_text("https://github.com/owner/repo\n")
    work_dir = tmp_path / "work"

    with (
        patch("main.read_repo_urls", return_value=["https://github.com/owner/repo"]),
        patch("main.find_labeled_items", return_value=[]) as mock_find,
        patch("main.load_state", return_value={}),
        patch("main.save_state"),
        patch("main.time.sleep", side_effect=StopIteration),
    ):
        try:
            import sys
            sys.argv = ["main", "--repos-file", str(repos_file), "--work-dir", str(work_dir)]
            m.main()
        except StopIteration:
            pass

    calls = mock_find.call_args_list
    assert len(calls) == 2
    label_sets = [c.args[1] for c in calls]
    assert m.ISSUE_LABELS in label_sets
    assert m.PR_LABELS in label_sets


def test_agent_ready_in_issue_labels():
    assert "agent-ready" in m.ISSUE_LABELS


def test_agent_ready_not_in_pr_labels():
    assert "agent-ready" not in m.PR_LABELS


# ---------------------------------------------------------------------------
# Step 3.2 — work_dir auto-creation
# ---------------------------------------------------------------------------


def test_work_dir_is_created_automatically(tmp_path):
    """main() must create work_dir with mkdir -p semantics if it does not exist."""
    new_dir = tmp_path / "nested" / "work"
    assert not new_dir.exists()

    repos_file = tmp_path / "repos.txt"
    repos_file.write_text("")

    with (
        patch("main.read_repo_urls", return_value=[]),
        patch("main.load_state", return_value={}),
        patch("main.time.sleep", side_effect=StopIteration),
    ):
        import sys
        sys.argv = ["main", "--repos-file", str(repos_file), "--work-dir", str(new_dir)]
        try:
            m.main()
        except StopIteration:
            pass

    assert new_dir.exists()
    assert new_dir.is_dir()

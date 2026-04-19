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


# ---------------------------------------------------------------------------
# Dedup: fresh timestamp stored after agent run
# ---------------------------------------------------------------------------


def test_fresh_updated_at_stored_after_agent_run(tmp_path):
    """After invoke_agent returns, main() must store the post-run updatedAt,
    not the pre-scan value, so the agent's own PR comments do not re-trigger
    the loop on the next cycle."""
    repos_file = tmp_path / "repos.txt"
    repos_file.write_text("https://github.com/owner/repo\n")
    work_dir = tmp_path / "work"

    pre_run_ts = "2026-04-19T10:00:00Z"
    post_run_ts = "2026-04-19T10:05:00Z"  # agent posted a 🚀 comment

    fake_item = {
        "number": 1,
        "title": "fix",
        "updatedAt": pre_run_ts,
        "labels": [{"name": "agent-implement"}],
        "kind": "pr",
        "repo_url": "https://github.com/owner/repo",
    }

    saved_states = []

    def capture_save(path, state):
        saved_states.append(dict(state))

    import sys
    sys.argv = ["main", "--repos-file", str(repos_file), "--work-dir", str(work_dir)]

    with (
        patch("main.read_repo_urls", return_value=["https://github.com/owner/repo"]),
        patch("main.find_labeled_items", side_effect=[fake_item["labels"] and [fake_item], []]),
        patch("main.needs_processing", return_value=True),
        patch("main.provision", return_value=work_dir),
        patch("main.invoke_agent", return_value=0),
        patch("main.fetch_updated_at", return_value=post_run_ts),
        patch("main.load_state", return_value={}),
        patch("main.save_state", side_effect=capture_save),
        patch("main.time.sleep", side_effect=StopIteration),
    ):
        try:
            m.main()
        except StopIteration:
            pass

    assert saved_states, "save_state was never called"
    item_key = "https://github.com/owner/repo:pr:1"
    assert saved_states[0][item_key] == post_run_ts, (
        f"Expected post-run timestamp {post_run_ts!r} to be stored, "
        f"got {saved_states[0].get(item_key)!r}"
    )

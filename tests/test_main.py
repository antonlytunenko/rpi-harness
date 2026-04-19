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
# Step 3.1 — Startup configuration summary
# ---------------------------------------------------------------------------


def test_startup_summary(tmp_path):
    """main() must emit a startup log containing work_dir, interval, and repo URLs
    before the first time.sleep call (PLAN step 1.1)."""
    repos_file = tmp_path / "repos.txt"
    repos_file.write_text("https://github.com/owner/repo\n")
    work_dir = tmp_path / "work"

    known_urls = ["https://github.com/owner/repo"]
    sleep_calls = []
    info_calls = []

    def capture_sleep(_):
        raise StopIteration

    import sys
    sys.argv = ["main", "--repos-file", str(repos_file), "--work-dir", str(work_dir),
                "--interval", "42"]

    with (
        patch("main.read_repo_urls", return_value=known_urls) as mock_read,
        patch("main.find_labeled_items", return_value=[]),
        patch("main.logger") as mock_logger,
        patch("main.time.sleep", side_effect=capture_sleep),
    ):
        try:
            m.main()
        except StopIteration:
            pass

    all_info_msgs = [call.args for call in mock_logger.info.call_args_list]
    startup_msgs = [args for args in all_info_msgs if "harness starting" in (args[0] if args else "")]
    assert startup_msgs, "No startup summary log found"
    startup_args = startup_msgs[0]
    # Check work_dir, interval, and repo list are present
    assert str(work_dir) in startup_args or any(str(work_dir) in str(a) for a in startup_args)
    assert 42 in startup_args or any(42 == a for a in startup_args)
    assert known_urls in startup_args or any(known_urls == a for a in startup_args)


# ---------------------------------------------------------------------------
# Step 3.2 — Distinct case (a) message: no repositories configured
# ---------------------------------------------------------------------------


def test_no_repos_message(tmp_path):
    """When read_repo_urls returns [], main() must log a message about no repos
    configured that does NOT contain the old text and DOES mention the repos file
    (PLAN step 2.1)."""
    repos_file = tmp_path / "repos.txt"
    repos_file.write_text("")
    work_dir = tmp_path / "work"

    import sys
    sys.argv = ["main", "--repos-file", str(repos_file), "--work-dir", str(work_dir)]

    with (
        patch("main.read_repo_urls", return_value=[]),
        patch("main.logger") as mock_logger,
        patch("main.time.sleep", side_effect=StopIteration),
    ):
        try:
            m.main()
        except StopIteration:
            pass

    all_info_calls = mock_logger.info.call_args_list
    all_rendered = [call.args[0] % call.args[1:] if call.args else "" for call in all_info_calls]

    old_text = "no repositories to scan, sleeping"
    assert not any(old_text in msg for msg in all_rendered), (
        f"Old message still present: {all_rendered}"
    )
    assert any("configured" in msg or str(repos_file) in msg for msg in all_rendered), (
        f"Expected case-a message not found in: {all_rendered}"
    )


# ---------------------------------------------------------------------------
# Step 3.3 — Distinct case (b) message: repos scanned but no labeled items
# ---------------------------------------------------------------------------


def test_no_items_message(tmp_path):
    """When repos are configured but find_labeled_items always returns [], main()
    must emit a 'no labeled items found' message distinct from the case-a message
    (PLAN step 2.2)."""
    repos_file = tmp_path / "repos.txt"
    repos_file.write_text("https://github.com/owner/repo\n")
    work_dir = tmp_path / "work"

    import sys
    sys.argv = ["main", "--repos-file", str(repos_file), "--work-dir", str(work_dir)]

    with (
        patch("main.read_repo_urls", return_value=["https://github.com/owner/repo"]),
        patch("main.find_labeled_items", return_value=[]),
        patch("main.logger") as mock_logger,
        patch("main.time.sleep", side_effect=StopIteration),
    ):
        try:
            m.main()
        except StopIteration:
            pass

    all_info_calls = mock_logger.info.call_args_list
    all_rendered = [call.args[0] % call.args[1:] if call.args else "" for call in all_info_calls]

    # Must contain the case-b message
    assert any("no labeled items found" in msg for msg in all_rendered), (
        f"Expected case-b 'no labeled items found' message not found in: {all_rendered}"
    )
    # Must NOT match the case-a "configured" text (distinct messages)
    case_b_msgs = [msg for msg in all_rendered if "no labeled items found" in msg]
    case_a_msgs = [msg for msg in all_rendered if "configured" in msg]
    assert case_b_msgs != case_a_msgs, "Case-a and case-b messages must be distinct"

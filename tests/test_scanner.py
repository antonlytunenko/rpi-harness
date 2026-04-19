"""Tests for harness.scanner (PLAN step 3.2)."""
import json
import textwrap
from unittest.mock import MagicMock, patch

import pytest

from harness.scanner import find_labeled_items, read_repo_urls


def test_read_repo_urls_ignores_blank_lines(tmp_path):
    f = tmp_path / "repos.txt"
    f.write_text("\nhttps://github.com/owner/repo\n\n")
    assert read_repo_urls(str(f)) == ["https://github.com/owner/repo"]


def test_read_repo_urls_ignores_comment_lines(tmp_path):
    f = tmp_path / "repos.txt"
    f.write_text("# comment\nhttps://github.com/owner/repo\n")
    assert read_repo_urls(str(f)) == ["https://github.com/owner/repo"]


def test_read_repo_urls_strips_whitespace(tmp_path):
    f = tmp_path / "repos.txt"
    f.write_text("  https://github.com/owner/repo  \n")
    assert read_repo_urls(str(f)) == ["https://github.com/owner/repo"]


def test_find_labeled_items_calls_gh_and_parses_json():
    fake_issue = {"number": 1, "title": "bug", "updatedAt": "2026-01-01T00:00:00Z", "labels": [{"name": "agent-research"}]}
    fake_pr = {"number": 2, "title": "fix", "updatedAt": "2026-01-02T00:00:00Z", "labels": [{"name": "agent-plan"}]}

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        if "issue" in cmd:
            m.stdout = json.dumps([fake_issue])
        else:
            m.stdout = json.dumps([fake_pr])
        return m

    with patch("harness.scanner.subprocess.run", side_effect=fake_run) as mock_run:
        items = find_labeled_items("https://github.com/owner/repo", ["agent-research", "agent-plan"])

    assert len(items) == 2
    kinds = {i["kind"] for i in items}
    assert kinds == {"issue", "pr"}
    assert mock_run.call_count == 2


def test_find_labeled_items_handles_gh_failure():
    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stdout = ""
        return m

    with patch("harness.scanner.subprocess.run", side_effect=fake_run):
        items = find_labeled_items("https://github.com/owner/repo", ["agent-research"])

    assert items == []

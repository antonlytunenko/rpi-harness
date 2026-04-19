"""Tests for harness.scanner (PLAN step 3.2)."""
import json
import textwrap
from unittest.mock import MagicMock, patch

import pytest

from harness.scanner import fetch_updated_at, find_labeled_items, read_repo_urls


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


def test_fetch_updated_at_returns_timestamp_for_issue():
    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stdout = '{"updatedAt": "2026-04-19T10:00:00Z"}'
        return m

    with patch("harness.scanner.subprocess.run", side_effect=fake_run) as mock_run:
        result = fetch_updated_at("https://github.com/owner/repo", "issue", 42)

    assert result == "2026-04-19T10:00:00Z"
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[1] == "issue"
    assert "42" in called_cmd
    assert "--repo" in called_cmd


def test_fetch_updated_at_uses_pr_subcommand_for_pr():
    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stdout = '{"updatedAt": "2026-04-19T11:00:00Z"}'
        return m

    with patch("harness.scanner.subprocess.run", side_effect=fake_run) as mock_run:
        result = fetch_updated_at("https://github.com/owner/repo", "pr", 7)

    assert result == "2026-04-19T11:00:00Z"
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[1] == "pr"


def test_fetch_updated_at_returns_empty_string_on_failure():
    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stdout = ""
        return m

    with patch("harness.scanner.subprocess.run", side_effect=fake_run):
        result = fetch_updated_at("https://github.com/owner/repo", "pr", 7)

    assert result == ""

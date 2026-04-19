"""Tests for harness.runner (PLAN step 3.5)."""
from unittest.mock import MagicMock, call, patch

from harness.runner import invoke_agent


def test_invoke_agent_calls_gh_copilot_suggest():
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("harness.runner.subprocess.run", return_value=mock_result) as mock_run:
        invoke_agent("/some/path", "run harness")

    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert cmd[:4] == ["gh", "copilot", "suggest", "-t"]
    assert "shell" in cmd
    assert "run harness" in cmd


def test_invoke_agent_passes_cwd(tmp_path):
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("harness.runner.subprocess.run", return_value=mock_result) as mock_run:
        invoke_agent(str(tmp_path), "run harness")

    _, kwargs = mock_run.call_args
    assert kwargs["cwd"] == str(tmp_path)


def test_invoke_agent_returns_exit_code():
    mock_result = MagicMock()
    mock_result.returncode = 42

    with patch("harness.runner.subprocess.run", return_value=mock_result):
        code = invoke_agent("/some/path", "run harness")

    assert code == 42

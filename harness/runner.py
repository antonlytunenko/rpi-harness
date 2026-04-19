"""Runner module: invoke the GitHub Copilot CLI agent in a target repository."""
from __future__ import annotations

import subprocess


def invoke_agent(repo_path: str, prompt: str) -> int:
    """Run ``gh copilot suggest`` with *prompt* in *repo_path*.

    Args:
        repo_path: Absolute path to the cloned repository directory.
        prompt: The shell prompt passed to ``gh copilot suggest``.

    Returns:
        The process exit code.
    """
    result = subprocess.run(
        ["gh", "copilot", "--", "-p", prompt, "--allow-all-tools"],
        cwd=repo_path,
    )
    return result.returncode

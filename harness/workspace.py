"""Workspace module: provision isolated working directories for target repos."""
from __future__ import annotations

import logging
import pathlib
import shutil
import subprocess
import tempfile

logger = logging.getLogger(__name__)


def _skip_existing(src: str, dst: str) -> str:
    """Copy *src* to *dst* only when *dst* does not already exist."""
    if not pathlib.Path(dst).exists():
        shutil.copy2(src, dst)
    return dst


def provision(work_dir: str, repo_url: str, harness_root: str) -> pathlib.Path:
    """Clone *repo_url* into a unique subdir of *work_dir* and inject harness config.

    Args:
        work_dir: Base directory under which the unique subdir is created.
        repo_url: Full GitHub URL of the repository to clone.
        harness_root: Path to the harness repository root (provides ``.github/``).

    Returns:
        Path to the cloned repository directory.

    Raises:
        RuntimeError: When ``git clone`` exits with a non-zero status.
    """
    unique_dir = pathlib.Path(tempfile.mkdtemp(dir=work_dir))
    clone_dest = unique_dir / "repo"

    result = subprocess.run(
        ["git", "clone", repo_url, str(clone_dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("git clone failed for %s: %s", repo_url, result.stderr)
        raise RuntimeError(f"git clone failed for {repo_url}: {result.stderr}")

    harness_github = pathlib.Path(harness_root) / ".github"
    if harness_github.is_dir():
        shutil.copytree(
            str(harness_github),
            str(clone_dest / ".github"),
            dirs_exist_ok=True,
            copy_function=_skip_existing,
        )

    return clone_dest

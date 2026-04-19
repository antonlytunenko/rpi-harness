"""Scanner module: read repo URLs and find labelled issues/PRs via gh CLI."""
from __future__ import annotations

import json
import subprocess


def read_repo_urls(path: str) -> list[str]:
    """Return non-empty, non-comment lines from *path*."""
    urls: list[str] = []
    with open(path) as fh:
        for line in fh:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                urls.append(stripped)
    return urls


def find_labeled_items(repo_url: str, labels: list[str]) -> list[dict]:
    """Return issues and PRs in *repo_url* that carry any label in *labels*.

    Uses ``gh issue list`` and ``gh pr list`` with JSON output.
    Results include a ``kind`` key (``"issue"`` or ``"pr"``).
    """
    label_arg = ",".join(labels)
    items: list[dict] = []

    for kind, subcommand in (("issue", "issue"), ("pr", "pr")):
        result = subprocess.run(
            [
                "gh",
                subcommand,
                "list",
                "--repo",
                repo_url,
                "--label",
                label_arg,
                "--json",
                "number,title,updatedAt,labels",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            for entry in json.loads(result.stdout or "[]"):
                entry["kind"] = kind
                entry["repo_url"] = repo_url
                items.append(entry)

    return items


def fetch_updated_at(repo_url: str, kind: str, number: int) -> str:
    """Return the current ``updatedAt`` ISO string for *kind* #*number* in *repo_url*.

    Returns an empty string on failure so callers can fall back gracefully.
    """
    subcommand = "issue" if kind == "issue" else "pr"
    result = subprocess.run(
        [
            "gh",
            subcommand,
            "view",
            str(number),
            "--repo",
            repo_url,
            "--json",
            "updatedAt",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return json.loads(result.stdout).get("updatedAt", "")
    return ""

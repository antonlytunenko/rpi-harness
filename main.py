"""Polling entry-point for the rpi-harness run loop."""
from __future__ import annotations

import argparse
import logging
import pathlib
import time

from harness.runner import invoke_agent
from harness.scanner import find_labeled_items, read_repo_urls
from harness.workspace import provision

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ISSUE_LABELS = ["agent-ready"]
PR_LABELS = ["agent-research", "agent-plan", "agent-implement"]
HARNESS_ROOT = str(pathlib.Path(__file__).parent)


def main() -> None:
    parser = argparse.ArgumentParser(description="rpi-harness polling run loop")
    parser.add_argument(
        "--repos-file",
        default="repositories.txt",
        help="Path to file listing GitHub repository URLs (default: repositories.txt)",
    )
    parser.add_argument(
        "--work-dir",
        required=True,
        help="Directory under which temporary workspaces are created",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Poll interval in seconds (default: 300)",
    )
    args = parser.parse_args()

    pathlib.Path(args.work_dir).mkdir(parents=True, exist_ok=True)

    try:
        startup_repos = read_repo_urls(args.repos_file)
    except FileNotFoundError:
        logger.warning("repos file not found at startup: %s", args.repos_file)
        startup_repos = []
    logger.info(
        "harness starting: work_dir=%s interval=%ds repos=%s",
        args.work_dir,
        args.interval,
        startup_repos,
    )

    while True:
        try:
            repo_urls = read_repo_urls(args.repos_file)
        except FileNotFoundError:
            logger.warning("repos file not found: %s", args.repos_file)
            repo_urls = []

        if not repo_urls:
            logger.info(
                "no repositories configured or loaded (checked: %s), sleeping",
                args.repos_file,
            )
        labeled_items_found = 0
        for repo_url in repo_urls:
            items = (
                find_labeled_items(repo_url, ISSUE_LABELS)
                + find_labeled_items(repo_url, PR_LABELS)
            )
            for item in items:
                labeled_items_found += 1
                item_key = f"{repo_url}:{item['kind']}:{item['number']}"
                logger.info("processing %s", item_key)
                prompt = (
                    f"Run harness for {item['kind']} #{item['number']} "
                    f"in repository {repo_url}"
                )
                try:
                    clone_path = provision(args.work_dir, repo_url, HARNESS_ROOT)
                except RuntimeError as exc:
                    logger.error("provision failed, skipping %s: %s", item_key, exc)
                    continue

                exit_code = invoke_agent(str(clone_path), prompt)
                logger.info("agent exited with code %d for %s", exit_code, item_key)

        if repo_urls and labeled_items_found == 0:
            logger.info(
                "scan complete: no labeled items found across %d repository/repositories",
                len(repo_urls),
            )
        logger.info("sleeping %d seconds", args.interval)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

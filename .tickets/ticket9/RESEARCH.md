# Research: Harness Loop Does Not Work (Issue #9)

## Problem Analysis

Two distinct bugs were identified in the harness run loop:

### Bug 1: `agent-ready` issues are not detected

The harness loop is intended to detect GitHub issues labeled `agent-ready` and bootstrap them (create a branch, open a draft PR, apply `agent-research`). However, `AGENT_LABELS` in `main.py` (line 17) only contains `["agent-research", "agent-plan", "agent-implement"]`. The string `"agent-ready"` is absent. As a result, `find_labeled_items()` (scanner.py, line 22) never scans for `agent-ready`-labeled items, so the bootstrap path is never triggered.

### Bug 2: Missing `work_dir` is not created automatically

When `--work-dir` points to a non-existent directory, the loop fails silently or raises an unhandled error:

- `main.py` line 42 constructs `state_path` under `args.work_dir` without verifying the directory exists.
- `save_state()` in `dedup.py` line 21 calls `open(path, "w")`, which will raise `FileNotFoundError` if the parent directory does not exist.
- `provision()` in `workspace.py` line 39 calls `tempfile.mkdtemp(dir=work_dir)`, which also raises `FileNotFoundError` if `work_dir` does not exist.

No code path checks for the existence of `work_dir` or attempts to create it.

## Affected Files

| File | Lines | Role |
|---|---|---|
| `main.py` | 17, 42 | Entry point; defines `AGENT_LABELS`; constructs `state_path` from `work_dir` |
| `harness/scanner.py` | 22–50 | `find_labeled_items()` — filters items by labels passed to it |
| `harness/workspace.py` | 39 | `provision()` — calls `tempfile.mkdtemp(dir=work_dir)`, fails if dir missing |
| `harness/dedup.py` | 21 | `save_state()` — writes JSON, fails if parent dir missing |

## Technical Constraints

- Python 3 (uses `from __future__ import annotations`, `pathlib`, `argparse`).
- No framework; only stdlib + `gh` CLI subprocess calls.
- `AGENT_LABELS` list is defined once in `main.py` and passed to `find_labeled_items()`.
- `work_dir` is a CLI argument (argparse); it flows unchanged into `provision()`, `tempfile.mkdtemp()`, and `state_path` construction.
- Bootstrap logic (create branch, open PR, apply labels) is NOT implemented in `main.py` at all — only scanning for the three in-flight labels is present.

## Open Questions

1. Should the bootstrap logic (branch creation, PR creation, label mutation) be implemented inside `main.py` directly, or extracted to a new module (e.g. `harness/bootstrap.py`)?
   **Resolved**: Extract to a new module (`harness/bootstrap.py`). Source: PR comment by `antonlytunenko` on 2026-04-19.

2. When `work_dir` does not exist, should the loop create it (with `mkdir -p` semantics) and continue, or log an error and exit?
   **Resolved**: Create it (with `mkdir -p` semantics) and continue. Source: PR comment by `antonlytunenko` on 2026-04-19.

3. Should `agent-ready` scanning include both issues **and** PRs, or issues only?
   **Resolved**: Issues only for `agent-ready`; PRs should be scanned for `agent-research`, `agent-plan`, `agent-implement`. Source: PR comment by `antonlytunenko` on 2026-04-19.

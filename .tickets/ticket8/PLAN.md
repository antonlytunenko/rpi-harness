# Plan for Issue #8 — Improve Messages from Harness Loop

## Scope Boundary

### Included
- Add a one-time startup configuration summary log in `main.py` (before the `while True:` loop).
- Replace the existing "no repositories to scan, sleeping" message with a distinct message for case (a): no repositories configured or loaded.
- Add a new distinct message for case (b): repositories were scanned but no labeled items were found across any of them.
- Add tests in `tests/test_main.py` for each of the three new or changed messages.

### Excluded
- Changes to `harness/scanner.py`, `harness/dedup.py`, `harness/runner.py`, or `harness/workspace.py`.
- Changes to `README.md` or any documentation files.
- Changes to logging format, log level configuration, or log output destination.
- Any change to polling behaviour, scan logic, or dedup logic.
- Any change outside `main.py` and `tests/test_main.py`.

---

## Phase 1 — Startup Configuration Summary

### Step 1.1 — Read repos at startup and emit summary log

**Input**: `args.work_dir`, `args.interval`, and `args.repos_file` (available immediately after `parse_args()`); `read_repo_urls()` from `harness/scanner.py` (already imported).

**Output**: One `logger.info` call placed in `main.py` immediately after `pathlib.Path(args.work_dir).mkdir(...)` (line 44) and before the `while True:` loop. The message must contain: the resolved `args.work_dir` path, the poll interval in seconds, and the full normalized list of repository URLs returned by `read_repo_urls(args.repos_file)`. If the repos file is not found at startup, the warning branch logs the warning and the startup summary reflects an empty list — matching the existing error-handling pattern already used inside the loop.

**Dependency**: None (standalone addition before the loop).

**Verification**: Running `pytest -q tests/test_main.py -k startup` passes after Step 3.1 is written.

---

## Phase 2 — Distinct "Nothing Found" Messages

### Step 2.1 — Replace case (a): no repositories configured

**Input**: The `if not repo_urls:` branch inside the `while True:` loop (`main.py` around line 57), which currently logs `"no repositories to scan, sleeping"`.

**Output**: The existing `logger.info` call in that branch is replaced with a distinct message that identifies the condition as "no repositories configured or loaded" and includes `args.repos_file` so the operator knows which file was consulted. The replacement message must be textually different from the case (b) message added in Step 2.2.

**Dependency**: Step 1.1 must be complete (ensures startup read pattern is established and understood before touching the loop).

**Verification**: Running `pytest -q tests/test_main.py -k no_repos` passes after Step 3.2 is written.

### Step 2.2 — Add case (b): repos scanned but no labeled items found

**Input**: The body of the `for repo_url in repo_urls:` loop in `main.py` and the code immediately following it. Currently no message is emitted when all repositories yield zero matching labeled items.

**Output**: A counter or flag is introduced inside the loop to track whether at least one labeled item was encountered across all repositories in a single scan cycle. After the `for` loop completes, if `repo_urls` is non-empty but the counter shows zero items found, a `logger.info` call emits a distinct "scan complete: no labeled items found" message that includes the repository count. This message must be textually different from the case (a) message.

**Dependency**: Step 2.1 must be complete (loop structure is stable before adding post-loop state tracking).

**Verification**: Running `pytest -q tests/test_main.py -k no_items` passes after Step 3.3 is written.

---

## Phase 3 — Tests

### Step 3.1 — Test startup configuration summary

**Input**: `tests/test_main.py`; the `logger` object in `main.py` patched via `unittest.mock`.

**Output**: A new test function (name containing `startup`) that patches `read_repo_urls` to return a known list of URLs, runs `main()` until `time.sleep` raises `StopIteration`, and asserts that `logger.info` was called at least once with a message containing `args.work_dir`, `args.interval`, and the known URL list — before the first `time.sleep` call. The test must run in isolation (no filesystem side-effects beyond `tmp_path`).

**Dependency**: Step 1.1.

**Verification**: `pytest -q tests/test_main.py::test_startup_summary` exits 0.

### Step 3.2 — Test distinct case (a) message

**Input**: `tests/test_main.py`.

**Output**: A new test function (name containing `no_repos`) that patches `read_repo_urls` to return an empty list, runs `main()` until `time.sleep` raises `StopIteration`, and asserts that `logger.info` was called with a message that: (a) does NOT contain the old text `"no repositories to scan, sleeping"`, and (b) DOES contain a substring uniquely associated with the new case-a message (e.g., the repos file path or the word "configured").

**Dependency**: Step 2.1.

**Verification**: `pytest -q tests/test_main.py::test_no_repos_message` exits 0.

### Step 3.3 — Test distinct case (b) message

**Input**: `tests/test_main.py`.

**Output**: A new test function (name containing `no_items`) that patches `read_repo_urls` to return a non-empty list and patches `find_labeled_items` to return an empty list for all calls, runs `main()` until `time.sleep` raises `StopIteration`, and asserts that `logger.info` was called with a message that: (a) contains a substring uniquely associated with the case-b message (e.g., "no labeled items found" or similar), and (b) is not the same as the case-a message text.

**Dependency**: Step 2.2.

**Verification**: `pytest -q tests/test_main.py::test_no_items_message` exits 0.

---

## Dependency Summary

```
1.1  →  2.1  →  2.2
1.1  →  3.1
2.1  →  3.2
2.2  →  3.3
```

All five steps must complete before the final `pytest -q` is run across the whole test suite.

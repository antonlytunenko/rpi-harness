# Plan: Harness Loop Does Not Work (Issue #9)

## Phases and Steps

### Phase 1 — Fix `agent-ready` detection in `main.py`

**Step 1.1 — Add `"agent-ready"` to `AGENT_LABELS`**

- Input: `main.py` line 17 where `AGENT_LABELS` is defined.
- Output: `AGENT_LABELS` includes `"agent-ready"` as the first element.
- Grounding: RESEARCH.md § Bug 1 — `"agent-ready"` is absent from `AGENT_LABELS`, so `find_labeled_items()` never scans for it.
- Verification: `grep -n "agent-ready" main.py` returns a match on the `AGENT_LABELS` line.

**Step 1.2 — Split issue scanning from PR scanning in `main.py`**

- Input: `main.py` loop calling `find_labeled_items(repo_url, AGENT_LABELS)` for all labels over both issues and PRs.
- Output: Issues are scanned for `["agent-ready"]` only; PRs are scanned for `["agent-research", "agent-plan", "agent-implement"]` only. Results are merged before the processing loop.
- Grounding: RESEARCH.md § Open Question 3 (Resolved) — `agent-ready` is issues-only; `agent-research`, `agent-plan`, `agent-implement` are PRs-only. Source: PR comment by `antonlytunenko` on 2026-04-19.
- Dependencies: Step 1.1 must be complete (so both label sets are defined).
- Verification: `grep -n "find_labeled_items" main.py` shows two distinct calls with different label lists.

### Phase 2 — Create `harness/bootstrap.py`

**Step 2.1 — Create `harness/bootstrap.py` with a `bootstrap_issue()` function**

- Input: Nothing exists at `harness/bootstrap.py`.
- Output: `harness/bootstrap.py` contains a `bootstrap_issue(repo_url, issue_number, issue_title)` function that:
  1. Creates a branch named `issue-<number>/<slug>` in the target repo.
  2. Opens a draft PR linked to the issue.
  3. Applies the `agent-research` label to the PR.
  4. Removes the `agent-ready` label from the issue.
- Grounding: RESEARCH.md § Bug 1 — bootstrap logic is absent. RESEARCH.md § Open Question 1 (Resolved) — extract to a new module. Source: PR comment by `antonlytunenko` on 2026-04-19.
- Verification: `python -c "from harness.bootstrap import bootstrap_issue"` exits with code 0.

**Step 2.2 — Call `bootstrap_issue()` from `main.py` for `agent-ready` items**

- Input: `main.py` processing loop currently calls `provision()` and `invoke_agent()` for every matched item regardless of kind.
- Output: When an item's label is `"agent-ready"`, `main.py` calls `bootstrap_issue()` (imported from `harness.bootstrap`) instead of `provision()` / `invoke_agent()`. Other items continue to use the existing path.
- Grounding: RESEARCH.md § Bug 1 — bootstrap path is never triggered.
- Dependencies: Step 2.1 must be complete (module must exist before it can be imported).
- Verification: `grep -n "bootstrap_issue" main.py` returns a match.

### Phase 3 — Create `work_dir` automatically

**Step 3.1 — Add `mkdir -p` call for `work_dir` in `main.py` before the polling loop**

- Input: `main.py` line 42 constructs `state_path` under `args.work_dir` without ensuring the directory exists.
- Output: A single `pathlib.Path(args.work_dir).mkdir(parents=True, exist_ok=True)` call is inserted after argument parsing and before the `while True` loop.
- Grounding: RESEARCH.md § Bug 2 — `save_state()` and `provision()` both raise `FileNotFoundError` when `work_dir` is absent. RESEARCH.md § Open Question 2 (Resolved) — create with `mkdir -p` semantics and continue. Source: PR comment by `antonlytunenko` on 2026-04-19.
- Verification: `grep -n "mkdir" main.py` returns a match; running `python main.py --repos-file /dev/null --work-dir /tmp/new-test-dir` creates `/tmp/new-test-dir` without error.

### Phase 4 — Tests

**Step 4.1 — Add unit test for `agent-ready` detection split**

- Input: Existing test suite (look for `tests/` directory).
- Output: A test that patches `find_labeled_items` and asserts it is called once for issues with `["agent-ready"]` and once for PRs with the three in-flight labels.
- Grounding: RESEARCH.md § Affected Files — `main.py` and `scanner.py` are both affected.
- Dependencies: Steps 1.1 and 1.2 must be complete.
- Verification: `pytest tests/ -q -k "agent_ready"` passes.

**Step 4.2 — Add unit test for `bootstrap_issue()`**

- Input: `harness/bootstrap.py` from Step 2.1.
- Output: A test that patches `subprocess.run` and asserts the expected `gh` CLI calls are made with correct arguments.
- Grounding: RESEARCH.md § Affected Files — `harness/bootstrap.py` is a new module.
- Dependencies: Step 2.1 must be complete.
- Verification: `pytest tests/ -q -k "bootstrap"` passes.

**Step 4.3 — Add unit test for `work_dir` auto-creation**

- Input: `main.py` after Step 3.1.
- Output: A test that invokes the `work_dir` creation path with a non-existent directory path and asserts the directory is created.
- Grounding: RESEARCH.md § Bug 2 — missing directory causes `FileNotFoundError`.
- Dependencies: Step 3.1 must be complete.
- Verification: `pytest tests/ -q -k "work_dir"` passes.

## Dependencies Summary

```
1.1 → 1.2
1.1, 1.2 → 4.1
2.1 → 2.2
2.1 → 4.2
3.1 → 4.3
```

## Verification (full suite)

After all steps are complete:

```
pytest -q
```

All tests must pass with exit code 0.

## Scope Boundary

### Included

- Adding `"agent-ready"` to `AGENT_LABELS` in `main.py`.
- Splitting issue/PR scanning calls in `main.py` so `agent-ready` is issues-only.
- Creating `harness/bootstrap.py` with `bootstrap_issue()`.
- Wiring `bootstrap_issue()` into `main.py` for `agent-ready` items.
- Adding `mkdir -p` for `work_dir` in `main.py`.
- Unit tests for each of the above changes.

### Excluded

- Changes to `harness/scanner.py` internals beyond what is needed to support the split calls.
- Changes to `harness/dedup.py` or `harness/workspace.py`.
- Any feature not documented in RESEARCH.md or the resolved open questions.
- Retry logic for `bootstrap_issue()` failures.
- Modifications to `repositories.txt` or any configuration file.

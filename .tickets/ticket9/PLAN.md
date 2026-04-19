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

### Phase 2 — Create `work_dir` automatically

**Step 2.1 — Add `mkdir -p` call for `work_dir` in `main.py` before the polling loop**

- Input: `main.py` line 42 constructs `state_path` under `args.work_dir` without ensuring the directory exists.
- Output: A single `pathlib.Path(args.work_dir).mkdir(parents=True, exist_ok=True)` call is inserted after argument parsing and before the `while True` loop.
- Grounding: RESEARCH.md § Bug 2 — `save_state()` and `provision()` both raise `FileNotFoundError` when `work_dir` is absent. RESEARCH.md § Open Question 2 (Resolved) — create with `mkdir -p` semantics and continue. Source: PR comment by `antonlytunenko` on 2026-04-19.
- Verification: `grep -n "mkdir" main.py` returns a match; running `python main.py --repos-file /dev/null --work-dir /tmp/new-test-dir` creates `/tmp/new-test-dir` without error.

### Phase 3 — Tests

**Step 3.1 — Add unit test for `agent-ready` detection split**

- Input: Existing test suite (look for `tests/` directory).
- Output: A test that patches `find_labeled_items` and asserts it is called once for issues with `["agent-ready"]` and once for PRs with the three in-flight labels.
- Grounding: RESEARCH.md § Affected Files — `main.py` and `scanner.py` are both affected.
- Dependencies: Steps 1.1 and 1.2 must be complete.
- Verification: `pytest tests/ -q -k "agent_ready"` passes.

**Step 3.2 — Add unit test for `work_dir` auto-creation**

- Input: `main.py` after Step 2.1.
- Output: A test that invokes the `work_dir` creation path with a non-existent directory path and asserts the directory is created.
- Grounding: RESEARCH.md § Bug 2 — missing directory causes `FileNotFoundError`.
- Dependencies: Step 2.1 must be complete.
- Verification: `pytest tests/ -q -k "work_dir"` passes.

## Dependencies Summary

```
1.1 → 1.2
1.1, 1.2 → 3.1
2.1 → 3.2
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
- Adding `mkdir -p` for `work_dir` in `main.py`.
- Unit tests for each of the above changes.

### Excluded

- Bootstrap phase (`harness/bootstrap.py` and `bootstrap_issue()`) — removed per PR comment by `antonlytunenko` on 2026-04-19.
- Changes to `harness/scanner.py` internals beyond what is needed to support the split calls.
- Changes to `harness/dedup.py` or `harness/workspace.py`.
- Any feature not documented in RESEARCH.md or the resolved open questions.
- Modifications to `repositories.txt` or any configuration file.

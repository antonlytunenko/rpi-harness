# Plan: Harness Loop State Persistence (#17)

## Overview

The dedup state file is tied to the ephemeral `--work-dir` and can be lost on restart.
The resolution (per human feedback on 2026-04-19) is:

1. **No state file** — since the Python loop won't read or write it, there is no reason
   to create one at all. Removing the state file from scope entirely.
2. **Label-based, unconditional processing** — the Python loop moves to a purely
   label-based model: if an item carries a phase label it is processed **on every poll
   cycle**. There is no change-detection at the harness level.
3. **Agent-level idempotency handles "nothing new"** — each agent invocation begins
   with Step 0 (comment detection). If it finds no unprocessed human comments (no new
   comments since the last 👀 reaction was applied), it reaches STOP within seconds
   without invoking any expensive operations. This is the correct layer for dedup: the
   harness dispatches unconditionally; the agent decides whether real work is needed.
4. Temp-directory cleanup is explicitly **out of scope** per research resolution.

### Why no harness-level change detection?

All meaningful user actions — new comment, new review comment, label change — update the
GitHub item's `updated_at` field. The original dedup compared `updated_at` against a
locally cached timestamp. That cache is unreliable because it was stored in the ephemeral
`work_dir`. Replacing it with a GitHub-based approach (e.g., compare `updated_at` against
the timestamp of the last 🚀 comment) would work but adds complexity with no clear
benefit: agent Step 0 already provides correct idempotency at low cost. Processing every
labeled item unconditionally keeps the harness loop simple and correct.

Source: PR comments by `antonlytunenko` on 2026-04-19.

---

## Phase 1: Remove all state file management from `main.py`

### Step 1.1 — Delete the `state_path` constant and all state load/save calls

**Input**: `main.py` — the following lines exist:
- `from harness.dedup import load_state, needs_processing, save_state` (import)
- `state_path = str(pathlib.Path(args.work_dir) / ".harness_state.json")`
- `state = load_state(state_path)` inside the loop
- `if not needs_processing(state, item_key, updated_at): … continue`
- `fresh = fetch_updated_at(…)` and `state[item_key] = fresh or updated_at`
- `save_state(state_path, state)`

**Output**:
- Remove the `load_state`, `needs_processing`, `save_state` names from the
  `harness.dedup` import (leave `harness.dedup` importable if still needed elsewhere,
  or drop the import entirely if nothing else in `main.py` uses it)
- Remove the `state_path = …` line
- Remove `state = load_state(state_path)` from the loop
- Remove the `needs_processing` guard block (every labeled item is now processed)
- Remove `fresh = fetch_updated_at(…)`, `state[item_key] = …`, `save_state(…)`
- Remove `fetch_updated_at` from the `harness.scanner` import if it is now unused

**Dependency**: None  
**Verification**:
```
grep -n "state_path\|load_state\|save_state\|needs_processing\|fetch_updated_at" main.py
```
returns no output

---

## Phase 2: Update tests

### Step 2.1 — Remove or update mocks that reference the removed state helpers

**Input**: `tests/test_main.py` — likely contains `patch("main.load_state")`,
`patch("main.save_state")`, `patch("main.needs_processing")`,
`patch("main.fetch_updated_at")` calls, and any assertions on `state_path`  
**Output**: All such patches and assertions removed or replaced with the new
no-state-file behaviour  
**Dependency**: Step 1.1  
**Verification**: `pytest tests/test_main.py -q` exits 0 with no skipped tests

### Step 2.2 — Verify dedup unit tests are unaffected

**Input**: `tests/test_dedup.py`  
**Output**: No changes required (the dedup module itself is unchanged; only `main.py`
stopped calling it)  
**Dependency**: None  
**Verification**: `pytest tests/test_dedup.py -q` exits 0

---

## Dependency Summary

```
Step 1.1 → Step 2.1
Step 2.2 (independent)
```

---

## Scope Boundary

### Included

- Removal of all state file load/save/path logic from `main.py`
- Removal of any now-unused imports in `main.py` (`load_state`, `save_state`,
  `needs_processing`, `fetch_updated_at`)
- Test updates to reflect the no-state-file model

### Excluded

- Any changes to `harness/dedup.py` (module kept as-is for potential future use)
- Any `--state-file` CLI argument
- Temp-directory cleanup after `invoke_agent()` (explicitly out of scope)
- Changes to `harness/workspace.py`, `harness/runner.py`, `harness/scanner.py`
- Any README or documentation updates
- Harness mode instruction (harness.md) updates — state management spec is a
  separate concern tracked outside this ticket

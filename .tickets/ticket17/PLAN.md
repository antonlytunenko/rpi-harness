# Plan: Harness Loop State Persistence (#17)

## Overview

The dedup state file is tied to the ephemeral `--work-dir` and can be lost on restart.
The resolution (per human feedback on 2026-04-19) is that the **harness loop Python
code must not manage the state file at all** — no reading, no writing. State lifecycle
(creation → update after each processing step) is exclusively owned by the harness
copilot agent (the mode instructions in harness.md). The Python loop moves to a
purely label-based dedup model: if an item carries a phase label it is processed; the
agent is responsible for idempotency when nothing has changed. Temp-directory cleanup
is explicitly **out of scope** per research resolution.

Source: PR comments by `antonlytunenko` on 2026-04-19 —  
"Harness loop (python code) must not manage state file at all. It must be managed by
harness copilot agent (harness.md): from creation to state update after each
processing step."

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

## Phase 2: Create and commit the initial state file (agent-owned artifact)

### Step 2.1 — Create `.tickets/ticket17/harness_state.json`

**Input**: Nothing (new file)  
**Output**: `.tickets/ticket17/harness_state.json` with content `{}`  
**Dependency**: None (independent of Phase 1)  
**Verification**: `cat .tickets/ticket17/harness_state.json` prints `{}`

Note: this file is established by this harness agent run as part of the PR. It is the
initial state artifact that future harness agent invocations will read and update via
git commits. No Python runtime code creates, reads, or modifies it.

---

## Phase 3: Update tests

### Step 3.1 — Remove or update mocks that reference the removed state helpers

**Input**: `tests/test_main.py` — likely contains `patch("main.load_state")`,
`patch("main.save_state")`, `patch("main.needs_processing")`,
`patch("main.fetch_updated_at")` calls, and any assertions on `state_path`  
**Output**: All such patches and assertions removed or replaced with the new
no-state-file behaviour  
**Dependency**: Step 1.1  
**Verification**: `pytest tests/test_main.py -q` exits 0 with no skipped tests

### Step 3.2 — Verify dedup unit tests are unaffected

**Input**: `tests/test_dedup.py`  
**Output**: No changes required (the dedup module itself is unchanged; only `main.py`
stopped calling it)  
**Dependency**: None  
**Verification**: `pytest tests/test_dedup.py -q` exits 0

---

## Dependency Summary

```
Step 1.1 → Step 3.1
Step 2.1 (independent)
Step 3.2 (independent)
```

---

## Scope Boundary

### Included

- Removal of all state file load/save/path logic from `main.py`
- Removal of any now-unused imports in `main.py` (`load_state`, `save_state`,
  `needs_processing`, `fetch_updated_at`)
- Initial empty state file at `.tickets/ticket17/harness_state.json` (created by
  this agent as part of the PR; not touched by Python runtime code)
- Test updates to reflect the no-state-file model

### Excluded

- Any changes to `harness/dedup.py` (module kept as-is for potential future use)
- Any `--state-file` CLI argument
- Temp-directory cleanup after `invoke_agent()` (explicitly out of scope)
- Changes to `harness/workspace.py`, `harness/runner.py`, `harness/scanner.py`
- Any README or documentation updates
- Harness mode instruction (harness.md) updates — state management spec is a
  separate concern tracked outside this ticket

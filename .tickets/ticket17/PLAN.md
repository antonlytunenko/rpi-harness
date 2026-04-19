# Plan: Harness Loop State Persistence (#17)

## Overview

The dedup state file is currently anchored to the ephemeral `--work-dir`, which means
it is lost whenever the harness restarts with a new directory. The fix is to decouple
the state file path from `work_dir` by computing it from `HARNESS_ROOT` and the fixed
ticket number directly in Python — no CLI argument. The initial empty state file is
created by the harness agent (copilot) as part of this PR; the harness Python code only
reads/writes it. Temp-directory cleanup is explicitly **out of scope** per research
resolution.

Source: PR comment by `antonlytunenko` on 2026-04-19 — "State file PATH can not be
passed as an argument, because this path is TICKET specific. … state file should be
established by harness agent, not by harness loop python code."

---

## Phase 1: Replace the ephemeral `state_path` computation in `main.py`

### Step 1.1 — Remove the `work_dir`-relative `state_path` line

**Input**: Line `state_path = str(pathlib.Path(args.work_dir) / ".harness_state.json")`
in `main.py`  
**Output**: Replace it with
`state_path = str(pathlib.Path(__file__).parent / ".tickets" / "ticket17" / "harness_state.json")`  
**Dependency**: None  
**Verification**: `grep "work_dir.*harness_state" main.py` returns no output;
`grep "ticket17/harness_state" main.py` returns the new line

---

## Phase 2: Create and commit the initial state file

### Step 2.1 — Create `.tickets/ticket17/harness_state.json`

**Input**: Nothing (new file)  
**Output**: `.tickets/ticket17/harness_state.json` with content `{}`  
**Dependency**: None (independent of Phase 1)  
**Verification**: `cat .tickets/ticket17/harness_state.json` prints `{}`

Source: RESEARCH.md resolution — "check in state file as part of the PR in
`.tickets/ticket17/` directory." This file is established by the harness agent as
part of this PR, not by any runtime Python code.

---

## Phase 3: Update and add tests

### Step 3.1 — Verify existing tests are unaffected

**Input**: `tests/test_main.py`, `tests/test_dedup.py`  
**Output**: All existing tests still pass; no test body changes required (existing
tests mock `load_state`/`save_state` and do not depend on `state_path`)  
**Dependency**: Phase 1 complete  
**Verification**: `pytest tests/test_main.py tests/test_dedup.py -q` exits 0

### Step 3.2 — Add a test for the hardcoded `state_path` value

**Input**: `tests/test_main.py`  
**Output**: New test `test_state_path_is_within_harness_root` that calls
`build_state_path()` (a thin helper extracted from `main.py` in Step 1.1) or
inspects the constant directly, asserting it contains `ticket17/harness_state.json`
and is an absolute path  
**Dependency**: Step 1.1  
**Verification**: New test is collected and passes

---

## Dependency Summary

```
Step 1.1 → Step 3.2
Step 2.1 (independent)
Steps 1.1, 2.1 → Step 3.1
```

---

## Scope Boundary

### Included

- Replacement of the `work_dir`-relative `state_path` line in `main.py` with a
  hardcoded path derived from `__file__` and the ticket number
- Initial empty state file at `.tickets/ticket17/harness_state.json` (created by
  the agent as part of this PR)
- One new unit test verifying the hardcoded state path

### Excluded

- Any `--state-file` CLI argument (explicitly rejected per human feedback)
- Temp-directory cleanup after `invoke_agent()` (explicitly decided not to implement;
  see RESEARCH.md resolution for question 2)
- Changes to `harness/dedup.py`, `harness/workspace.py`, or any other module
- Any README or documentation updates
- Migration of an existing state file

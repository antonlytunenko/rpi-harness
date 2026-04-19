# Plan: Harness Loop State Persistence (#17)

## Overview

The dedup state file is currently anchored to the ephemeral `--work-dir`, which means
it is lost whenever the harness restarts with a new directory. The fix is to decouple
the state file path from `work_dir` by introducing a `--state-file` CLI argument whose
default points inside the harness repo root (a version-controlled, persistent location).
Temp-directory cleanup is explicitly **out of scope** per research resolution.

---

## Phase 1: Add `--state-file` argument to `main.py`

### Step 1.1 — Add the argument

**Input**: `main.py`, `argparse` block  
**Output**: New `--state-file` optional argument with default
`{HARNESS_ROOT}/.tickets/ticket17/harness_state.json`  
**Dependency**: None  
**Verification**: `python main.py --help` output includes `--state-file`

Source: RESEARCH.md "Dedup state storage" resolution — store state at a path within the
harness repo root so it is version-controlled and survives process restarts.

### Step 1.2 — Replace the hard-coded `state_path` computation

**Input**: Line `state_path = str(pathlib.Path(args.work_dir) / ".harness_state.json")`
in `main.py`  
**Output**: `state_path = args.state_file`  
**Dependency**: Step 1.1  
**Verification**: Running `grep "work_dir.*harness_state" main.py` returns no output

---

## Phase 2: Create and commit the initial state file

### Step 2.1 — Create `.tickets/ticket17/harness_state.json`

**Input**: Nothing (new file)  
**Output**: `.tickets/ticket17/harness_state.json` with content `{}`  
**Dependency**: None (independent of Phase 1)  
**Verification**: `cat .tickets/ticket17/harness_state.json` prints `{}`  
Source: RESEARCH.md resolution — "check in state file as part of the PR in
`.tickets/ticket17/` directory."

---

## Phase 3: Update and add tests

### Step 3.1 — Verify existing tests are unaffected

**Input**: `tests/test_main.py`  
**Output**: Confirm all existing tests mock `load_state`/`save_state` and therefore do
not depend on `state_path`; no changes needed to existing test bodies  
**Dependency**: Phase 1 complete  
**Verification**: `pytest tests/test_main.py tests/test_dedup.py -q` exits 0

### Step 3.2 — Add a test for the new default `--state-file` path

**Input**: `tests/test_main.py`  
**Output**: New test `test_default_state_file_is_within_harness_root` that asserts
`HARNESS_ROOT` appears in the default value of the `--state-file` argument parsed by
`argparse`; does not invoke `main()` or touch the filesystem  
**Dependency**: Step 1.1  
**Verification**: New test is collected and passes

---

## Dependency Summary

```
Step 1.1 → Step 1.2
Step 2.1 (independent)
Step 1.1 → Step 3.2
Steps 1.1, 1.2, 2.1 → Step 3.1
```

---

## Scope Boundary

### Included

- `--state-file` CLI argument in `main.py` with default inside `HARNESS_ROOT`
- Removal of the `work_dir`-relative `state_path` computation
- Initial empty state file at `.tickets/ticket17/harness_state.json`
- One new unit test verifying the default path

### Excluded

- Temp-directory cleanup after `invoke_agent()` (explicitly decided not to implement; see RESEARCH.md resolution for question 2)
- Changes to `harness/dedup.py`, `harness/workspace.py`, or any other module
- Any README or documentation updates
- Migration of an existing state file

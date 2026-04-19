# Research: Harness Loop State Issue (#17)

## Problem Analysis

The issue reports that the harness loop loads state on every run to identify changes in PRs and Issues, but every run creates a NEW directory that has no state.

There are two distinct problems identified:

### Problem 1: Dedup state is tied to an ephemeral `work_dir`

`main.py:44` stores the dedup state file at `{work_dir}/.harness_state.json`:

```
state_path = str(pathlib.Path(args.work_dir) / ".harness_state.json")
```

`main.py:59` reloads this file at the top of every poll cycle:

```
state = load_state(state_path)
```

`main.py:104-105` saves updated timestamps back to this file after each agent run:

```
state[item_key] = fresh or updated_at
save_state(state_path, state)
```

This design is only correct if `work_dir` is **the same persistent path** across every restart of `main.py`. If the harness is restarted with a different `--work-dir`, or if `work_dir` is ephemeral (e.g., `/tmp` cleared on reboot, or a fresh Docker volume), the state file is absent. `load_state()` returns `{}` (`harness/dedup.py:10-13`), and `needs_processing({}, key, ts)` returns `True` for all items (`harness/dedup.py:24-28`). Result: every labeled item is re-processed on every process restart regardless of whether it was already handled.

### Problem 2: Temp directories created by `provision()` are never cleaned up

`harness/workspace.py:22` creates a new temporary subdirectory for every item processed:

```
unique_dir = pathlib.Path(tempfile.mkdtemp(dir=work_dir))
```

`harness/workspace.py:23` clones the repo into it:

```
clone_dest = unique_dir / "repo"
```

There is no cleanup call anywhere after `invoke_agent()` returns (`main.py:96`). These directories accumulate indefinitely: one full git clone per item per poll cycle, never removed. Over time this causes unbounded disk usage growth.

### Desired behavior (from issue body)

> "Make sure, that every new run is stateless and always is run in new directory. In future, new run can be a separate docker container."

Each agent invocation (each call to `invoke_agent`) should run in a fresh, isolated directory — this part is already implemented. The question is how the dedup layer should survive process restarts given that agent runs are designed to be stateless and ephemeral.

## Affected Files

| File | Role |
|---|---|
| `main.py` | Entry point; contains the poll loop, state load/save calls (lines 44, 59, 103-105), and `provision()` call (line 91) |
| `harness/dedup.py` | Implements `load_state`, `save_state`, `needs_processing` — the entire dedup mechanism |
| `harness/workspace.py` | Implements `provision()` — creates the temp dir and clones the repo; no cleanup logic |
| `harness/runner.py` | Invokes the agent in the clone path; not related to state management |
| `harness/scanner.py` | Fetches items from GitHub; returns `updatedAt` timestamps used by dedup |
| `tests/test_main.py` | Tests for the run loop; mocks `load_state`/`save_state` |
| `tests/test_dedup.py` | Tests for `load_state`, `save_state`, `needs_processing` |
| `tests/test_workspace.py` | Tests for `provision()`; does not test cleanup behavior |

## Technical Constraints

- Python 3 with `pathlib`, `tempfile`, `subprocess` (no third-party deps in core modules).
- Dedup currently relies on ISO-8601 string comparison (`harness/dedup.py:28`): `updated_at_iso > stored`.
- `provision()` copies `.github/` from the harness root into the clone with `_skip_existing` semantics (`workspace.py:35-42`); this logic must be preserved.
- Tests use `patch("main.load_state")` and `patch("main.save_state")` — any signature change to these functions will require test updates.
- The `gh` CLI is the sole GitHub API interface; no direct API calls are made.

## Open Questions

1. **Where should the dedup state be stored?** The current `{work_dir}/.harness_state.json` location is lost on restart with a new `work_dir`. Options include: (a) a fixed well-known path independent of `work_dir`, (b) a `--state-file` CLI argument, (c) no local state (rely purely on the GitHub API — e.g., check if a 🚀 comment was already posted), or (d) keep current behavior and document that `work_dir` must be persistent.
   **RESOLVED** (Source: PR comment by `antonlytunenko` on 2026-04-19): Check in the state file as part of the PR in `.tickets/ticket<ticket_number>/` directory.

2. **Should the temp directories created by `provision()` be cleaned up after each agent run?** If yes, after `invoke_agent()` returns (success or failure), the `unique_dir` should be removed with `shutil.rmtree`. If no, callers must be aware of the disk usage growth.
   **RESOLVED** (Source: PR comment by `antonlytunenko` on 2026-04-19): Do not clean up directories.

3. **Is eliminating the state file the goal, or just making it resilient?** The issue says "every new run is stateless" — does this mean the harness process itself should carry no local state across restarts, or only that each individual agent invocation runs in a fresh directory?
   **RESOLVED** (Source: PR comment by `antonlytunenko` on 2026-04-19): The second interpretation — each individual agent invocation runs in a fresh directory. The harness process itself may maintain persistent state (the state file) across restarts, stored in `.tickets/ticket<ticket_number>/` within the PR branch.

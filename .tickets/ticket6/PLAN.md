# Plan: Harness Run Loop (Issue #6)

## Scope Boundary

### Included
- `pyproject.toml` updated with `pytest` as a dev optional-dependency
- `repositories.txt` file created with one commented-out example entry explaining the expected format (full GitHub URLs, one per line)
- `harness/` Python package with four modules: scanner, dedup, workspace, runner
- `main.py` replaced with a polling entry-point that parses CLI arguments and drives the loop
- Unit tests for each of the four modules under `tests/`

### Excluded
- Changes to `.github/agents/harness.md`, instruction files, or prompt files
- Any GUI, web interface, or systemd service unit
- Parallel or multi-threaded polling
- Authentication configuration beyond inheriting the caller's `gh` auth context
- Automatic phase-label advancement or PR/issue creation by the polling script itself (those remain the agent's responsibility when it runs in a target repository)
- Packaging, distribution, or Docker containerisation

---

## Phase 1: Project Setup

### Step 1.1 — Add pytest dev dependency
**Depends on**: nothing  
**Input**: `pyproject.toml` with `dependencies = []` and no optional-dependencies table  
**Output**: `pyproject.toml` has a `[project.optional-dependencies]` table with a `dev` key that includes `pytest`  
**Verification**: `pip install -e .[dev] && pytest --version` exits 0

### Step 1.2 — Create `repositories.txt`
**Depends on**: nothing  
**Input**: file does not exist  
**Output**: `repositories.txt` exists at the repository root; contains at least one commented-out example line showing the expected full GitHub URL format  
**Verification**: `test -f repositories.txt` exits 0

---

## Phase 2: Core Modules

### Step 2.1 — Create `harness/` package
**Depends on**: nothing  
**Input**: no `harness/` directory exists  
**Output**: `harness/__init__.py` exists (may be empty); `harness/` is importable as a Python package  
**Verification**: `python -c "import harness"` exits 0

### Step 2.2 — Create `harness/scanner.py`
**Depends on**: Step 2.1  
**Input**: `harness/` package exists; `gh` CLI available on PATH  
**Output**: `harness/scanner.py` exports a function `read_repo_urls(path) -> list[str]` that reads non-empty, non-comment lines from a given file, and a function `find_labeled_items(repo_url, labels) -> list[dict]` that uses `gh issue list` and `gh pr list` (via `subprocess`) to return issues/PRs carrying any of the specified labels for the given repository URL  
**Verification**: `python -c "from harness.scanner import read_repo_urls, find_labeled_items"` exits 0

### Step 2.3 — Create `harness/dedup.py`
**Depends on**: Step 2.1  
**Input**: `harness/` package exists  
**Output**: `harness/dedup.py` exports a function `load_state(path) -> dict` that reads a JSON file (returning `{}` if it does not exist), a function `save_state(path, state)` that writes the dict as JSON, and a function `needs_processing(state, item_key, updated_at_iso) -> bool` that returns `True` when `updated_at_iso` is later than the timestamp stored in `state` for `item_key` (or when no record exists)  
**Verification**: `python -c "from harness.dedup import load_state, save_state, needs_processing"` exits 0

### Step 2.4 — Create `harness/workspace.py`
**Depends on**: Step 2.1  
**Input**: `harness/` package exists; `git` available on PATH; harness repo root path is known at call time  
**Output**: `harness/workspace.py` exports a function `provision(work_dir, repo_url, harness_root) -> pathlib.Path` that:  
  1. Creates a unique subdirectory under `work_dir`  
  2. Clones `repo_url` into it using `git clone` (via `subprocess`); logs and raises `RuntimeError` on failure so the caller can skip  
  3. Copies the harness `.github/` directory tree into the clone using `shutil.copytree` with `dirs_exist_ok=True` and a `copy_function` that skips files already present in the destination  
  4. Returns the path to the cloned repository directory  
**Verification**: `python -c "from harness.workspace import provision"` exits 0

### Step 2.5 — Create `harness/runner.py`
**Depends on**: Step 2.1  
**Input**: `harness/` package exists; `gh` CLI available on PATH  
**Output**: `harness/runner.py` exports a function `invoke_agent(repo_path, prompt) -> int` that changes the working directory to `repo_path` and executes `gh copilot suggest -t shell "<prompt>"`, returning the process exit code  
**Verification**: `python -c "from harness.runner import invoke_agent"` exits 0

### Step 2.6 — Replace `main.py` with polling entry-point
**Depends on**: Steps 2.2, 2.3, 2.4, 2.5  
**Input**: `main.py` contains the placeholder stub  
**Output**: `main.py` is replaced with a `main()` function that:  
  1. Parses three CLI arguments: `--repos-file` (default: `repositories.txt`), `--work-dir` (required), `--interval` (default: `300`, in seconds)  
  2. Derives `harness_root` as the directory containing `main.py` itself  
  3. Loads dedup state from `<work-dir>/.harness_state.json`  
  4. Enters an infinite loop that: reads repo URLs, calls `find_labeled_items` for each, checks `needs_processing` for each match, calls `provision` (skipping on `RuntimeError`), calls `invoke_agent`, updates and saves dedup state, then sleeps for `--interval` seconds  
**Verification**: `python main.py --help` exits 0 and prints usage including `--repos-file`, `--work-dir`, and `--interval`

---

## Phase 3: Tests

### Step 3.1 — Create `tests/__init__.py`
**Depends on**: Step 2.1  
**Input**: no `tests/` directory  
**Output**: `tests/__init__.py` exists (empty)  
**Verification**: `test -f tests/__init__.py` exits 0

### Step 3.2 — Create `tests/test_scanner.py`
**Depends on**: Steps 2.2, 3.1  
**Input**: `harness/scanner.py` exists  
**Output**: `tests/test_scanner.py` contains:  
  - A test that `read_repo_urls` ignores blank lines and lines starting with `#`  
  - A test that `read_repo_urls` returns stripped URLs from valid lines  
  - A test that `find_labeled_items` calls the correct `gh` subcommands and parses JSON output (mocked via `unittest.mock.patch`)  
**Verification**: `pytest tests/test_scanner.py -q` exits 0

### Step 3.3 — Create `tests/test_dedup.py`
**Depends on**: Steps 2.3, 3.1  
**Input**: `harness/dedup.py` exists  
**Output**: `tests/test_dedup.py` contains:  
  - A test that `needs_processing` returns `True` when the key is absent from state  
  - A test that `needs_processing` returns `False` when the stored timestamp equals the item timestamp  
  - A test that `needs_processing` returns `True` when the item has a newer timestamp  
  - A test that `load_state` returns `{}` when the file does not exist  
  - A round-trip test: `save_state` then `load_state` returns the original dict  
**Verification**: `pytest tests/test_dedup.py -q` exits 0

### Step 3.4 — Create `tests/test_workspace.py`
**Depends on**: Steps 2.4, 3.1  
**Input**: `harness/workspace.py` exists  
**Output**: `tests/test_workspace.py` contains:  
  - A test that `provision` creates a subdirectory under `work_dir` (mocked `git clone`)  
  - A test that `provision` raises `RuntimeError` when `git clone` fails  
  - A test that `provision` copies the harness `.github/` into the clone using a temp harness root (no network call)  
  - A test that `provision` does not overwrite a file already present in the clone's `.github/`  
**Verification**: `pytest tests/test_workspace.py -q` exits 0

### Step 3.5 — Create `tests/test_runner.py`
**Depends on**: Steps 2.5, 3.1  
**Input**: `harness/runner.py` exists  
**Output**: `tests/test_runner.py` contains:  
  - A test that `invoke_agent` calls `gh copilot suggest` with the provided prompt (mocked `subprocess`)  
  - A test that `invoke_agent` passes `cwd=repo_path` to the subprocess call  
  - A test that `invoke_agent` returns the process exit code  
**Verification**: `pytest tests/test_runner.py -q` exits 0

---

## Phase 4: Full Verification

### Step 4.1 — Run full test suite
**Depends on**: all Phase 3 steps  
**Input**: all test files exist and no syntax errors  
**Output**: all tests collected by pytest pass  
**Verification**: `pytest -q` exits 0 with no failures or errors

---

## Dependencies Summary

```
1.1 ─┐
1.2  │
2.1 ─┼─ 2.2 ─┬─ 2.6
     ├─ 2.3 ─┤
     ├─ 2.4 ─┤
     └─ 2.5 ─┘
2.1 ─── 3.1 ─┬─ 3.2 (needs 2.2)
              ├─ 3.3 (needs 2.3)
              ├─ 3.4 (needs 2.4)
              └─ 3.5 (needs 2.5)
3.2, 3.3, 3.4, 3.5 ─── 4.1
```

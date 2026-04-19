# Research: Improve Messages from Harness Loop (Issue #8)

## Problem Analysis

- The run loop exposes the configured inputs via CLI arguments (`--repos-file`, `--work-dir`, `--interval`), creates the work directory, and then immediately enters the polling loop, but it never logs the resolved configuration values at startup. There is currently no message that tells the operator which work directory, interval, or repository list the process is using. (`main.py:23-44`)
- The only explicit "nothing to do" message today is `no repositories to scan, sleeping`, which is emitted only when the repository list is empty after reading `repositories.txt`. If configured repositories are present but none of them produce matching issues or PRs, the loop falls through to the generic `sleeping %d seconds` log with no message explaining that no actionable items were found. (`main.py:48-60`, `main.py:90-91`)
- The loop already emits per-item logs for `skipping`, `processing`, `provision failed`, and `agent exited`, so the missing operator feedback is specifically at startup and at the "zero matches this cycle" case rather than in the per-item processing path. (`main.py:64-80`)
- Existing tests for `main.py` cover label routing, automatic work-dir creation, and post-run timestamp refresh, but they do not assert any logging output or any behavior for a scan cycle that finds zero actionable items. There is no current regression coverage for the messaging requested in Issue #8. (`tests/test_main.py:17-135`)

## Affected Files

| File | Role |
| --- | --- |
| `main.py` | Defines the CLI arguments, startup setup, polling loop, and all current operator-facing log messages. The requested startup/configuration and "nothing found" messaging would be emitted from this file. (`main.py:23-91`) |
| `tests/test_main.py` | Existing unit tests exercise `main()` behavior and are the natural place to add regression coverage for any new logging or zero-match-cycle behavior. (`tests/test_main.py:17-135`) |
| `README.md` | Documents the runtime arguments and examples for `--work-dir`, `--repos-file`, and `--interval`; it may need to stay aligned if operator-visible startup messaging is documented or illustrated. (`README.md:44-90`) |

## Technical Constraints

- The project targets Python `>=3.11` and currently has no runtime dependencies declared, so any change should fit the existing stdlib-based approach already used in `main.py`. (`pyproject.toml:1-15`)
- `--work-dir` is required, while `--repos-file` defaults to `repositories.txt` and `--interval` defaults to `300`; these values are part of both the code-level CLI contract and the README usage documentation. (`main.py:23-39`, `README.md:44-72`)
- The loop creates `work_dir`, stores dedup state at `<work-dir>/.harness_state.json`, and then reloads state on each polling cycle. Any added messaging must coexist with that long-running loop structure. (`main.py:42-47`)
- The documented test runner is `pytest -q`, and the repository already includes pytest as a development dependency. (`README.md:87-90`, `pyproject.toml:9-15`)

## Open Questions

None at this stage.

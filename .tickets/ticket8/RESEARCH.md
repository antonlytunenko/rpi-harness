# Research: Improve messages from harness loop (Issue #8)

## Problem Analysis

Issue #8 requests clearer operator-facing output from the polling loop: the process should report its effective configuration at startup (work directory, poll interval, repositories) and should emit an explicit message when a poll cycle finds nothing to work on (Issue #8 body; PR #12 body).

The current entry point configures logging, parses `--repos-file`, `--work-dir`, and `--interval`, creates the work directory, and immediately enters the infinite polling loop. It does **not** log the resolved startup configuration after argument parsing, so the operator cannot confirm which work directory, interval, or repository list the process is using from the startup output alone (`main.py:14-18`, `main.py:22-45`).

The loop already logs some negative-path conditions, but only for specific cases. If `repositories.txt` is missing, the code logs `repos file not found: ...` and then continues with an empty repository list; if the repository list is empty, it logs `no repositories to scan, sleeping`; and at the end of every cycle it logs `sleeping %d seconds` (`main.py:48-56`, `main.py:85-86`).

However, when one or more repositories are configured **and** each call to `find_labeled_items(...)` returns no issues/PRs with matching labels, there is no cycle-level log explaining that nothing was found. In that path the code iterates over repositories, does not enter the inner `for item in items:` body, and then only emits the generic sleep message (`main.py:56-61`, `main.py:85-86`). This matches the issue report that the observable output can collapse to a sleep log when there is nothing actionable.

A second quiet path exists when matching items are returned but every item is skipped by deduplication. In that case the operator may see one or more `skipping ... (no new activity)` lines, but there is still no single summary that the cycle produced no actionable work (`main.py:61-66`).

The existing `main.py` tests validate label scanning behavior, automatic creation of the work directory, and post-run timestamp persistence, but they do not assert on log messages or other operator-facing output. Message behavior is therefore currently untested (`tests/test_main.py:17-135`).

## Affected Files

| File | Role | Why it is relevant |
|---|---|---|
| `main.py` | Polling loop entry point | Contains all current startup and per-cycle logging, CLI argument parsing, repository loading, item scanning, dedup skipping, and sleep behavior that issue #8 is asking to make more explicit (`main.py:14-18`, `main.py:22-86`). |
| `tests/test_main.py` | Unit tests for the run loop | Covers branch label scanning and work-dir creation only; it is the most direct place to add verification for new logging behavior later (`tests/test_main.py:17-78`). |
| `harness/scanner.py` | Repository list loading helper | Defines how repository URLs are read from disk, including comment/blank-line filtering, which constrains what “repositories” means in any startup message (`harness/scanner.py:8-16`). |
| `README.md` | User-facing CLI documentation | Documents the existing CLI arguments and examples, which are the configuration values the issue wants surfaced at runtime; it does not currently describe startup/no-work log output (`README.md:44-85`). |

## Technical Constraints

- The project targets Python `>=3.11` and has no runtime dependencies beyond the standard library at present; any message changes should fit within that environment (`pyproject.toml:1-15`).
- The current loop uses the standard-library `logging` module with a global `basicConfig(...)` setup and a module logger, so new operator messages should follow the same logging pathway to remain consistent with existing output formatting (`main.py:4-15`).
- Repository values come from `read_repo_urls(path)`, which returns non-empty, non-comment lines from a text file. Any startup message that includes repositories must either read from this helper or reproduce its filtering semantics exactly (`harness/scanner.py:8-16`).
- Missing repository files are already handled via `FileNotFoundError` in `main.py`, so startup/configuration reporting must account for the existing warning path where the configured file cannot be read (`main.py:48-52`).
- The process is an infinite polling loop that sleeps at the end of each cycle, and the current tests break out by patching `time.sleep`. Future verification of message behavior will likely need to use the same pattern rather than letting the loop run continuously (`main.py:46-86`, `tests/test_main.py:23-35`, `tests/test_main.py:65-75`).
- The README documents `--work-dir`, `--repos-file`, and `--interval` as the public CLI surface, so any new startup messaging should stay aligned with those argument names and meanings (`README.md:44-79`).

## Open Questions

All open questions resolved via PR comment by `antonlytunenko` (2026-04-19, comment #4276196693) and direct operator chat observation (2026-04-19).

1. ~~Should the requested "nothing found" message appear only when **no labeled issues/PRs are returned at all**, or also when items are returned but every item is skipped because `needs_processing(...)` reports no new activity?~~ **Resolved**: Both are distinct cases and must produce distinct messages. The goal is a message that is easy to interpret for the user — the two paths ("no labeled items found in this repo" vs "items found but all deduplication-skipped") should be highlighted differently so an operator can tell at a glance whether the repository has no actionable labels or whether it does but nothing new has happened since the last run. (Source: PR comment by `antonlytunenko` on 2026-04-19)

2. ~~Should "repositories" in the startup message be the fully resolved list or a summary?~~ **Resolved**: Log the full list of resolved repository URIs at startup. (Source: PR comment by `antonlytunenko` on 2026-04-19)


# Research: Harness Run Loop (Issue #6)

## Problem Analysis

The harness agent currently requires manual user invocation via VS Code ("Run harness"). Issue #6 requests an automated Python polling script that:
1. Continuously scans a list of GitHub repositories for labelled issues/PRs.
2. For each match, provisions an isolated working directory, clones required repos, injects the harness `.github` config, and invokes the GitHub Copilot CLI.
3. Loops every N minutes.

The harness state machine (research → plan → implement) itself is unchanged; only the triggering mechanism is being automated.

## Affected Files

| File | Role |
|---|---|
| `main.py` (line 1–5) | Current stub entry-point; will be replaced or extended to implement the loop |
| `pyproject.toml` (line 1–7) | Project metadata and dependency declaration; will need new runtime dependencies (e.g. `PyGithub` or `requests`) |
| `.github/agents/harness.md` (entire file) | Defines the harness agent that the CLI must invoke; referenced for `.github` dir copy step |
| `.github/instructions/*.md` | Instruction files copied alongside the agent definition into target repositories |
| `.github/prompts/*.md` | Prompt files also included in the `.github` copy step |
| `README.md` | Currently empty; not directly affected but may need documentation |

No `repositories.txt` file exists yet — it must be created as part of implementation.

## Technical Constraints

- Python `>=3.11` (from `pyproject.toml` line 6). Currently running Python 3.13.11.
- `gh` CLI v2.90.0 is available at `/opt/homebrew/bin/gh`; all GitHub API operations currently use it.
- **GitHub Copilot CLI**: The `copilot` binary found at `/Users/Anton_Lytunenko/Library/Application Support/Code/User/globalStorage/github.copilot-chat/copilotCli/copilot` reports "Cannot find GitHub Copilot CLI". This path is user-specific and not portable. Official installation path is unknown in this environment (see Open Questions).
- `git` must be available on PATH for clone operations.
- The script must not clobber files already in `{repo}/.github/` — copy only, no overrides on conflict.
- The work directory must be passed as a CLI argument.
- Poll interval N must be configurable (likely a CLI argument or env variable).
- No existing test suite; `pyproject.toml` has no `[tool.pytest]` or test deps declared.
- The existing `main.py` is a minimal stub with no logic (`print("Hello from rpi-harness!")`, line 2).
- `pyproject.toml` has an empty `dependencies = []` (line 7) — all new deps must be added here.

## Open Questions

All questions resolved via PR review by `antonlytunenko` on 2026-04-19 (review ID 4135825608).

1. **Copilot CLI invocation**: What is the correct, portable command to invoke the GitHub Copilot CLI agent with a given prompt?
   **Answer**: Use `gh copilot`.

2. **repositories.txt format**: Should the file contain just `owner/repo` slugs (one per line), or full GitHub URLs?
   **Answer**: Full GitHub URLs (one per line).

3. **Poll interval N**: Should N be a required CLI argument, an optional argument with a default, or read from a config file?
   **Answer**: Optional CLI argument with a default of 5 minutes.

4. **Deduplication**: If a matching issue/PR was already processed in a previous poll cycle, should the script skip it or create a new working directory each time?
   **Answer**: Check whether there was new activity after the latest code push. Skip if no new activity.

5. **Harness repository identity**: Should the script infer the harness repo from its own `git remote`, hard-code it, or accept it as an argument?
   **Answer**: Hard-code it for now.

6. **gh auth context**: Should the script inherit the calling user's `gh` auth token, or use a separate `GITHUB_TOKEN`?
   **Answer**: Inherit the calling user's `gh` auth (no separate token needed).

7. **Error handling on clone/copy failures**: What should happen if cloning the target repository fails?
   **Answer**: Log the error and skip — do not abort the loop.

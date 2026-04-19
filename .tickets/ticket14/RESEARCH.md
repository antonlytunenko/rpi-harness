# Research: Ignore Closed PR (Issue #14)

## Problem Analysis

The harness bootstrap rule currently says to create a branch and draft PR only when "no PR exists yet". That wording appears in both the agent instructions (`.github/agents/harness.md`) and the product spec (`.specs/harness-spec-001.md`). It is too broad for the restart scenario described in issue #14: if a previous PR for the issue was closed, a historical PR still exists, but it should not block creating a fresh replacement PR.

This means the bootstrap decision must be based on whether an **open** PR already exists for the issue, not whether **any** PR has ever existed. Otherwise the harness can get stuck after a failed attempt: the issue may be relabeled `agent-ready`, but the agent would incorrectly conclude that bootstrap is disallowed because a closed PR is still present in GitHub history.

At present, the repository does not implement bootstrap logic in Python (`main.py` only scans and dispatches work; there is no `bootstrap_issue()` or similar runtime path). So the currently broken behavior is encoded primarily in the harness workflow documentation/prompt, not in executable application code. Any later bootstrap implementation will also need the same "ignore closed PRs" rule to avoid diverging from the documented state machine.

## Affected Files

| File | Role |
|---|---|
| `.github/agents/harness.md` | Authoritative agent workflow; currently says bootstrap occurs only if "no PR exists yet". |
| `.specs/harness-spec-001.md` | Product/spec wording for the bootstrap trigger; currently says "No PR exists". |
| `main.py` | Current polling loop that detects `agent-ready` issues, but does not yet implement bootstrap/open-PR filtering. Relevant as the future execution point if the documented rule is later codified in Python. |
| `harness/scanner.py` | Existing GitHub CLI scanning helper; likely reusable if future implementation needs to query PR state for a specific issue. |

## Technical Constraints

- Python 3.11+ project using stdlib plus `gh` CLI subprocess calls.
- GitHub operations are expected to go through `gh`, not direct API client libraries.
- The harness state machine must not self-advance phases; bootstrap only prepares the draft PR and applies `agent-research`.
- Current runtime code scans `agent-ready` issues and in-flight PR labels, but it does **not** yet contain branch/PR creation logic, so the immediate source of truth for this issue is the workflow/spec text.
- Existing ticket documentation pattern uses `.tickets/ticket<issue>/RESEARCH.md` with explicit sections for problem analysis, affected files, constraints, and open questions.

## Open Questions

1. When determining whether an issue already has an open PR, what GitHub relationship should the harness treat as authoritative: PR body text such as `Closes #<issue>`, explicit linked issues metadata, branch naming convention, or some combination?
2. Should the fix for issue #14 be limited to updating the harness/spec wording, or should planning also include adding executable bootstrap logic that enforces the same "ignore closed PRs; block on open PRs only" rule in Python?
3. If multiple historical PRs are closed and none are open, should the replacement PR always reuse the standard branch naming pattern (`issue-<number>/<slug>`), or should the workflow define a collision strategy for recreating work after a prior attempt?

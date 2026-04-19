---
applyTo: "**/*.{py,js,ts,go,rb}"
---

# Implement Phase Constraints

These rules apply whenever source files (`.py`, `.js`, `.ts`, `.go`, `.rb`) are active in context.

- **Every change must trace to a PLAN.md step.** Before writing any code, identify which step in `PLAN.md` authorises it. Reference the step in the commit message: `(PLAN step N.M)`.
- **Tests required for every new function.** Any new function, method, or behaviour change must be accompanied by at least one test that exercises it.
- **Tests required for every bug fix.** Add a regression test that would have caught the bug before the fix.
- **Never skip the test run.** After completing all steps, always execute the full test suite before declaring done.
- **Minimal changes only.** Do not refactor, rename, or improve code that is not directly required by the active plan step.
- **Do not modify `.tickets/ticket<issue_number>/RESEARCH.md` or `.tickets/ticket<issue_number>/PLAN.md`.** These are read-only references during the implement phase.
- **Do not push to main or master.** All commits go to the feature branch.
- **Do not mark the PR ready until tests are green.** If tests fail after 3 iterations, comment with the failure summary and stop.

---
mode: agent
description: Implement phase task — execute PLAN.md step by step, write code and tests, run tests (max 3 iterations), then notify human.
tools:
  - codebase
  - readFile
  - editFiles
  - runCommands
---

You are executing the **Implement** phase of the harness workflow.

## Inputs

- `.tickets/ticket<issue_number>/PLAN.md` (required — abort if missing)
- `.tickets/ticket<issue_number>/RESEARCH.md` (reference for context)

## Task

### Step 0 — Validate prerequisites

1. Read `.tickets/ticket<issue_number>/PLAN.md` in full.
2. Read `.tickets/ticket<issue_number>/RESEARCH.md` for context.
3. Detect the test runner:
   - If `pyproject.toml` or `setup.py` exists → test command is `pytest -q`
   - If `package.json` exists → test command is `npm test`
   - Otherwise → comment on PR asking human to specify and stop.

### Step 1 — Implement each plan step

For each numbered step in `.tickets/ticket<issue_number>/PLAN.md`, in dependency order:

1. Read the step (inputs, action, output, verification).
2. Write or modify the required source files.
3. Write or update tests that cover the behaviour introduced by this step.
4. Reference the step in every commit:
   ```
   git add <files>
   git commit -m "<type>: <description> (PLAN step N.M)"
   ```

**Rules:**
- Every new function or changed behaviour must have a corresponding test.
- Never skip writing tests for a step.
- Do not implement anything not listed in `.tickets/ticket<issue_number>/PLAN.md`.

### Step 2 — Test loop (max 3 iterations)

After all steps are implemented:

**Iteration 1:**

```
<test command>
```

- If **all tests pass** → go to **Step 3 (green path)**.
- If **tests fail** → go to iteration 2.

**Iteration 2:**

1. Read the full test failure output carefully.
2. Identify the root cause (do not guess — read stack traces and assertion messages).
3. Apply the minimal fix. Do not refactor unrelated code.
4. Re-run tests.
- If **all tests pass** → go to **Step 3 (green path)**.
- If **tests fail** → go to iteration 3.

**Iteration 3:**

1. Repeat root-cause analysis and minimal fix.
2. Re-run tests.
- If **all tests pass** → go to **Step 3 (green path)**.
- If **tests still fail** → go to **Step 4 (red path)**.

### Step 3 — Green path (tests pass)

```
git push
gh pr ready
gh pr comment --body "Implementation complete. All tests pass. Ready for human review."
```

**STOP.**

### Step 4 — Red path (tests fail after 3 iterations)

```
git add -A
git commit -m "wip: failing tests after 3 iterations"
git push
gh pr comment --body "⚠️ Tests still failing after 3 fix iterations. Failure summary:

\`\`\`
<full test output from last run>
\`\`\`

Human intervention required."
```

**STOP. Do not attempt further fixes.**

## Constraints

- Every change must trace to a `.tickets/ticket<issue_number>/PLAN.md` step — reference it in commit messages.
- Do **not** modify `.tickets/ticket<issue_number>/RESEARCH.md` or `.tickets/ticket<issue_number>/PLAN.md`.
- Do **not** push directly to `main` or `master`.
- Do **not** mark the PR ready for review unless all tests pass.
- Do **not** exceed 3 test iterations.

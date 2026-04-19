---
mode: agent
description: Plan phase task — read RESEARCH.md and produce a concrete, traceable PLAN.md. Do not write code.
tools:
  - readFile
  - editFiles
  - runCommands
---

You are executing the **Plan** phase of the harness workflow.

## Inputs

- `.tickets/ticket<issue_number>/RESEARCH.md` (required — abort if missing)

## Task

1. Read `.tickets/ticket<issue_number>/RESEARCH.md` in full.
2. Verify that all Open Questions in `.tickets/ticket<issue_number>/RESEARCH.md` are resolved (have answers, not just "1. ..."). If any are unresolved, comment on the PR and stop:

```
gh pr comment --body "Cannot plan: RESEARCH.md contains unresolved open questions. Please answer them and re-trigger."
```

3. Write `.tickets/ticket<issue_number>/PLAN.md` in the repo root with the following structure:

```markdown
# Plan: <issue title>

## Scope

### Included
<!-- Bullet list of everything this plan will deliver. -->

### Excluded
<!-- Bullet list of what is explicitly out of scope for this change. -->

## Phases and Steps

### Phase 1 — <name>

**Step 1.1 — <name>**
- Input: <what this step reads or depends on>
- Action: <what to do, precisely>
- Output: <files created/modified, or observable result>
- Verification: `<command to confirm success>`
- Depends on: <step numbers, or "none">

**Step 1.2 — <name>**
...

### Phase 2 — <name>
...

## Dependency Graph
<!-- Ordered list of steps in execution order, respecting dependencies. -->
1. Step 1.1
2. Step 1.2
...

## Verification Checklist
<!-- One assertion per plan step that proves it is complete. -->
- [ ] Step 1.1: `<verification command or observable outcome>`
- [ ] Step 1.2: ...
```

4. Commit and push:

```
git add .tickets/ticket<issue_number>/PLAN.md
git commit -m "plan: implementation plan for #<number>"
git push
```

5. Comment on the PR:

```
gh pr comment --body "Plan complete. .tickets/ticket<issue_number>/PLAN.md committed. Please review and change label to \`agent-implement\` when ready."
```

## Constraints

- Do **not** write any source code or test code.
- Every step must reference findings from `.tickets/ticket<issue_number>/RESEARCH.md` — no speculation beyond the research scope.
- Do **not** modify `.tickets/ticket<issue_number>/RESEARCH.md`.
- Scope boundary (included/excluded) must be explicit and complete.

---
mode: agent
description: Research phase task — analyze the codebase and issue, then produce RESEARCH.md. Do not write implementation code.
tools:
  - codebase
  - readFile
  - editFiles
  - runCommands
---

You are executing the **Research** phase of the harness workflow.

## Inputs

- The linked GitHub issue (read via `gh issue view <number>`)
- The full codebase (`#codebase`)

## Task

1. Read the issue description carefully.
2. Explore every file in the codebase that could be relevant to the issue using `#codebase`.
3. Identify:
   - What is broken or missing
   - Which files need to change and why
   - Existing patterns, conventions, and constraints that must be respected
   - Any unknowns that require human clarification before a safe plan can be written
4. Write `.tickets/ticket<issue_number>/RESEARCH.md` in the repo root with the following sections:

```markdown
# Research: <issue title>

## Problem Analysis
<!-- What is broken or needed, and why. Reference specific line numbers where helpful. -->

## Affected Files
<!-- List each relevant file with a one-line description of its role and what may need to change. -->
| File | Role | Change needed |
|---|---|---|

## Technical Constraints
<!-- Language version, dependency versions, coding conventions, patterns that must not break. -->

## Open Questions
<!-- Anything that must be answered by a human before planning can begin. Number each item. -->
1. ...
```

5. Commit and push:

```
git add RESEARCH.md
git commit -m "research: initial analysis for #<number>"
git push
```

6. Comment on the PR:

```
gh pr comment --body "Research complete. RESEARCH.md committed. Please review open questions and change label to \`agent-plan\` when ready."
```

## Constraints

- Do **not** write any implementation code or propose concrete solutions.
- Do **not** create or modify any source files other than `.tickets/ticket<issue_number>/RESEARCH.md`.
- If the open questions section is empty, write "None — ready to plan."

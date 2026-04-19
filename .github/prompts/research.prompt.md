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

## Iteration (re-invocation)

If this is a re-invocation (the agent is called again while the PR still has `agent-research`):

1. Fetch PR comments: `gh pr view --json comments --jq '.comments[] | {id: .databaseId, body: .body}'`
2. Identify unprocessed human comments: body does **not** contain 🚀 **and** does not have a 👀 reaction.
   - If no 🚀 comment exists yet, treat all human comments as unprocessed.
3. If unprocessed human comments exist:
   a. Re-read `.tickets/ticket<issue_number>/RESEARCH.md` in full.
   b. For each unprocessed comment, identify which open question it answers or what new finding it introduces.
   c. Mark each comment with a 👀 reaction: `gh api repos/{owner}/{repo}/issues/comments/{comment_id}/reactions -f content=eyes`
   d. Update the Open Questions section of `RESEARCH.md` — mark resolved questions with their answers, citing comment author and date.
   e. Commit and push: `git add .tickets/ticket<issue_number>/RESEARCH.md && git commit -m "research: update with human feedback for #<N>" && git push`
   f. Post a PR comment summarising which questions were resolved. **Append 🚀 to the comment body.**
   g. **STOP.**
4. If no unprocessed human comments, run the normal first-run task below.

## Constraints

- Do **not** write any implementation code or propose concrete solutions.
- Do **not** create or modify any source files other than `.tickets/ticket<issue_number>/RESEARCH.md`.
- If the open questions section is empty, write "None — ready to plan."
- **Append 🚀 to every PR comment** this agent posts.

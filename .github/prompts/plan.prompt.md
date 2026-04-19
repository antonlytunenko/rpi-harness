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

## Iteration (re-invocation)

If this is a re-invocation (the agent is called again while the PR still has `agent-plan`):

1. Fetch PR comments: `gh pr view --json comments --jq '.comments[] | {id: .databaseId, body: .body}'`
2. Identify unprocessed human comments: body does **not** contain 🚀 **and** does not have a 👀 reaction.
3. If unprocessed human comments exist **and** `.tickets/ticket<issue_number>/PLAN.md` already exists:
   a. Re-read `.tickets/ticket<issue_number>/PLAN.md` in full.
   b. For each unprocessed comment, identify the feedback it provides.
   c. Mark each comment with a 👀 reaction: `gh api repos/{owner}/{repo}/issues/comments/{comment_id}/reactions -f content=eyes`
   d. Update `PLAN.md` — add or modify steps as needed, appending a "Source: PR comment by `<author>` on `<date>`" note.
   e. Commit and push: `git add .tickets/ticket<issue_number>/PLAN.md && git commit -m "plan: update with human feedback for #<N>" && git push`
   f. Post a PR comment summarising changes made. **Append 🚀 to the comment body.**
   g. **STOP.**
4. If no unprocessed human comments or `PLAN.md` does not exist yet, run the normal first-run task below.

## Constraints

- Do **not** write any source code or test code.
- Every step must reference findings from `.tickets/ticket<issue_number>/RESEARCH.md` — no speculation beyond the research scope.
- PR comment findings are also valid sources, provided they are cited with the comment author and date.
- Do **not** modify `.tickets/ticket<issue_number>/RESEARCH.md`.
- Scope boundary (included/excluded) must be explicit and complete.
- **Append 🚀 to every PR comment** this agent posts.

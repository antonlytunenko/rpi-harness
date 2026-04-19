# Plan: Make harness iterate based on user comment

## Scope

### Included

- Add a **comment-detection procedure** to `harness.md` that identifies human PR comments using emoji-based discrimination: the agent always appends 🚀 to its own comments (making them unambiguously identifiable regardless of `author.login`), and marks each processed human comment with a 👀 reaction via the GitHub API. Unprocessed human comments are comments that lack 🚀 in their body and lack a 👀 reaction. *(Source: PR comment by antonlytunenko on 2026-04-19)*
- Update the **Research phase** in `harness.md` to detect re-invocation and iterate on human comment answers: re-read `RESEARCH.md`, resolve open questions, commit updated research, and comment with a change summary.
- Update the **Plan phase** in `harness.md` to detect re-invocation and iterate on human comment feedback: re-read `PLAN.md`, incorporate feedback (citing source), commit the updated plan, and comment with a change summary.
- Update the **Implement phase** in `harness.md` to read human PR comments before beginning implementation on re-invocation, incorporating any feedback into the work.
- Update the per-phase prompt files (`research.prompt.md`, `plan.prompt.md`, `implement.prompt.md`) to mirror the new iteration logic for consistency.
- Update `plan.instructions.md` to clarify that PR comment findings are valid sources (in addition to `RESEARCH.md` findings), satisfying RESEARCH.md Q5.
- Update `research.instructions.md` to allow incorporating PR comment answers to open questions.

### Excluded

- No Python or shell orchestrator scripts. All behaviour remains in Markdown configuration files.
- No changes to `main.py`.
- No automatic re-trigger mechanism. The harness remains manually invoked by the user.
- No changes to the label-based state machine (label transitions still require human action).
- No GitHub Actions workflow changes.
- No changes to `implement.instructions.md` (its `applyTo` selector targets source files, not harness configuration; the implement phase behaviour is fully captured in `harness.md` and `implement.prompt.md`).

---

## Phases and Steps

### Phase 1 — Add comment-detection procedure to `harness.md`

**Step 1.1 — Insert "Comment Detection" section into `harness.md`**
- Input: `.github/agents/harness.md` (current content, read before edit)
- Action: Insert a new "Comment Detection" section immediately after the State Machine section and before the Bootstrap section. The section must specify:
  - **Agent comment identification**: agent comments always contain 🚀 in their body. The agent must append 🚀 to every PR comment it posts. This makes agent comments unambiguously identifiable even when `author.login` is shared with the human.
  - **Human comment identification**: comments whose body does NOT contain 🚀.
  - **Unprocessed human comments**: human comments that do NOT have a 👀 reaction. These are the comments that require iteration.
  - **Command to fetch comments with IDs**: `gh pr view --json comments --jq '.comments[] | {id: .databaseId, body: .body}'`
  - **Command to mark a comment as processed** (add 👀 reaction): `gh api repos/{owner}/{repo}/issues/comments/{comment_id}/reactions -f content=eyes` where `{owner}/{repo}` is obtained from `gh repo view --json nameWithOwner --jq '.nameWithOwner'` and `{comment_id}` is the `databaseId` from the comment list.
  - **Edge case**: if no 🚀 comment exists yet (first invocation), all human comments are treated as unprocessed first-run context.
  - The agent must mark each human comment it reads with 👀 before committing, so re-invocations do not re-process already-handled comments.
- Output: `.github/agents/harness.md` with new "Comment Detection" section inserted.
- Verification: `grep -n "Comment Detection" .github/agents/harness.md` returns a line number; `grep -n "rocket\|🚀" .github/agents/harness.md` returns a result.
- Depends on: none

### Phase 2 — Update Research phase in `harness.md`

**Step 2.1 — Add iteration branch to the Research phase procedure**
- Input: `.github/agents/harness.md` with Phase 1 changes applied
- Action: In the "Phase: Research" section, prepend a Step 0 before the existing steps:
  - Step 0: Run comment detection (per the Comment Detection section). If unprocessed human comments are found (iteration mode): (a) re-read `.tickets/ticket<N>/RESEARCH.md`; (b) for each unprocessed human comment, identify which open question it answers or what new finding it introduces; (c) mark each comment with a 👀 reaction immediately after reading it; (d) update the Open Questions section of `RESEARCH.md` — mark resolved questions with their answers, citing the comment author and date; (e) commit with `git commit -m "research: update with human feedback for #<N>"`; (f) post a PR comment summarising which questions were resolved (append 🚀 to the comment); (g) STOP. If no unprocessed human comments: continue with the existing first-run steps (steps 1–6 as currently defined).
- Output: `.github/agents/harness.md` with iteration-aware Research phase.
- Verification: `grep -n "iteration mode" .github/agents/harness.md | grep -i research` returns at least one match.
- Depends on: Step 1.1

### Phase 3 — Update Plan phase in `harness.md`

**Step 3.1 — Add iteration branch to the Plan phase procedure**
- Input: `.github/agents/harness.md` with Phase 2 changes applied
- Action: In the "Phase: Plan" section, prepend a Step 0:
  - Step 0: Run comment detection. If unprocessed human comments are found AND `.tickets/ticket<N>/PLAN.md` already exists (iteration mode): (a) re-read `PLAN.md`; (b) for each unprocessed human comment, identify the feedback it provides; (c) mark each comment with a 👀 reaction immediately after reading it; (d) update `PLAN.md` to incorporate the feedback — add or modify steps as needed, appending a "Source: PR comment by <author> on <date>" note; (e) commit with `git commit -m "plan: update with human feedback for #<N>"`; (f) post a PR comment summarising changes made (append 🚀 to the comment); (g) STOP. If no unprocessed human comments OR `PLAN.md` does not exist yet: continue with the existing first-run steps (steps 1–5).
- Output: `.github/agents/harness.md` with iteration-aware Plan phase.
- Verification: `grep -n "iteration mode" .github/agents/harness.md | grep -i plan` returns at least one match.
- Depends on: Step 2.1

### Phase 4 — Update Implement phase in `harness.md`

**Step 4.1 — Add comment-reading step to the Implement phase procedure**
- Input: `.github/agents/harness.md` with Phase 3 changes applied
- Action: In the "Phase: Implement" section, add to "Step 0 — Validate prerequisites" (or insert a new Step 0 before the existing validate step):
  - Run comment detection. If unprocessed human comments are found: read each comment and note any additional constraints, requirements, or clarifications they introduce; mark each with a 👀 reaction immediately after reading it. These inputs must be incorporated when implementing the relevant plan steps. Cite each source in the commit message if a human comment directly influenced a change: `(per PR comment by <author> <date>)`.
  - All agent PR comments during implementation must include 🚀.
  - If no unprocessed human comments: proceed normally.
- Output: `.github/agents/harness.md` with comment-aware Implement phase.
- Verification: `grep -n "human comments" .github/agents/harness.md | grep -i implement` returns at least one match, OR the implement section contains the phrase "human comments".
- Depends on: Step 3.1

### Phase 5 — Update per-phase prompt files

**Step 5.1 — Update `research.prompt.md`**
- Input: `.github/prompts/research.prompt.md`
- Action: Add a new "## Iteration (re-invocation)" section after the existing "## Task" section. The section must mirror the iteration logic from Step 2.1: detect unprocessed human comments (no 🚀 in body, no 👀 reaction); if found, mark them with 👀, update `RESEARCH.md` with answers, commit, and post a 🚀-suffixed PR comment; if not, run the normal first-run task.
- Output: `.github/prompts/research.prompt.md` with iteration section.
- Verification: `grep -n "Iteration" .github/prompts/research.prompt.md` returns a match.
- Depends on: Step 2.1

**Step 5.2 — Update `plan.prompt.md`**
- Input: `.github/prompts/plan.prompt.md`
- Action: Add a new "## Iteration (re-invocation)" section after the existing "## Task" section, mirroring Step 3.1 logic (detect unprocessed human comments via 🚀/👀 approach; mark with 👀, update plan, post 🚀-suffixed comment).
- Output: `.github/prompts/plan.prompt.md` with iteration section.
- Verification: `grep -n "Iteration" .github/prompts/plan.prompt.md` returns a match.
- Depends on: Step 3.1

**Step 5.3 — Update `implement.prompt.md`**
- Input: `.github/prompts/implement.prompt.md`
- Action: In the "Step 0 — Validate prerequisites" section (or as a new Step 0), add: read PR comments using comment detection; if unprocessed human comments exist (no 🚀 in body, no 👀 reaction), mark them with 👀 and note any constraints to incorporate. All agent comments in this phase must include 🚀. Mirror Step 4.1 logic.
- Output: `.github/prompts/implement.prompt.md` with comment-reading in Step 0.
- Verification: `grep -n "human comments\|PR comments" .github/prompts/implement.prompt.md` returns a match.
- Depends on: Step 4.1

### Phase 6 — Update instruction files

**Step 6.1 — Update `plan.instructions.md`**
- Input: `.github/instructions/plan.instructions.md`
- Action: Amend the bullet "Reference RESEARCH.md findings. Every step must be grounded in a finding from `RESEARCH.md`." to clarify that PR comment findings are also valid sources, provided they are cited with the comment author and date. This addresses RESEARCH.md Q5.
- Output: `.github/instructions/plan.instructions.md` with amended traceability rule.
- Verification: `grep -n "PR comment" .github/instructions/plan.instructions.md` returns a match.
- Depends on: none

**Step 6.2 — Update `research.instructions.md`**
- Input: `.github/instructions/research.instructions.md`
- Action: Add a bullet: "On re-invocation (iteration mode), PR comments that answer open questions are valid findings. Incorporate the answer into `RESEARCH.md`, cite the comment author and date, and mark the question as resolved."
- Output: `.github/instructions/research.instructions.md` with iteration bullet.
- Verification: `grep -n "re-invocation\|iteration" .github/instructions/research.instructions.md` returns a match.
- Depends on: none

---

## Dependency Graph

1. Step 1.1 — Insert Comment Detection section into `harness.md`
2. Step 2.1 — Add iteration branch to Research phase (depends on 1.1)
3. Step 3.1 — Add iteration branch to Plan phase (depends on 2.1)
4. Step 4.1 — Add comment-reading step to Implement phase (depends on 3.1)
5. Step 5.1 — Update `research.prompt.md` (depends on 2.1)
6. Step 5.2 — Update `plan.prompt.md` (depends on 3.1)
7. Step 5.3 — Update `implement.prompt.md` (depends on 4.1)
8. Step 6.1 — Update `plan.instructions.md` (independent)
9. Step 6.2 — Update `research.instructions.md` (independent)

Steps 6.1 and 6.2 are independent and can be done in any order or in parallel with steps 1–7.

---

## Verification Checklist

- [ ] Step 1.1: `grep -n "Comment Detection" .github/agents/harness.md` returns a result; `grep -n "🚀\|rocket" .github/agents/harness.md` returns a result; `grep -n "👀\|eyes" .github/agents/harness.md` returns a result
- [ ] Step 2.1: `grep -n "iteration mode" .github/agents/harness.md` returns a result in the Research section
- [ ] Step 3.1: `grep -n "iteration mode" .github/agents/harness.md` returns a result in the Plan section
- [ ] Step 4.1: The Implement section in `harness.md` contains the phrase "human comments"
- [ ] Step 5.1: `grep -n "Iteration" .github/prompts/research.prompt.md` returns a result
- [ ] Step 5.2: `grep -n "Iteration" .github/prompts/plan.prompt.md` returns a result
- [ ] Step 5.3: `grep -n "human comments\|PR comments" .github/prompts/implement.prompt.md` returns a result
- [ ] Step 6.1: `grep -n "PR comment" .github/instructions/plan.instructions.md` returns a result
- [ ] Step 6.2: `grep -n "re-invocation\|iteration" .github/instructions/research.instructions.md` returns a result

# Plan: Make harness iterate based on user comment

## Scope

### Included

- Add a **comment-detection procedure** to `harness.md` that identifies human PR comments posted after the last agent comment, using timestamp-based discrimination.
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
  - Command to fetch comments: `gh pr view --json comments --jq '.comments[]'`
  - Agent comment patterns (known phrase prefixes that uniquely identify agent-authored comments, since agent and human share the same `author.login`): `"Research complete."`, `"Research updated."`, `"Plan complete."`, `"Implementation complete."`, `"Cannot plan:"`, `"⚠️ Tests still failing"`
  - Definition of "last agent comment timestamp": `createdAt` of the most recent comment whose body starts with or contains any of the above patterns.
  - Definition of "human comments": all comments whose `createdAt` is strictly after the last agent comment timestamp.
  - Edge case: if no agent comment exists yet, all comments are treated as first-run context (no iteration).
- Output: `.github/agents/harness.md` with new "Comment Detection" section inserted.
- Verification: `grep -n "Comment Detection" .github/agents/harness.md` returns a line number.
- Depends on: none

### Phase 2 — Update Research phase in `harness.md`

**Step 2.1 — Add iteration branch to the Research phase procedure**
- Input: `.github/agents/harness.md` with Phase 1 changes applied
- Action: In the "Phase: Research" section, prepend a Step 0 before the existing steps:
  - Step 0: Run comment detection (per the Comment Detection section). If human comments are found (iteration mode): (a) re-read `.tickets/ticket<N>/RESEARCH.md`; (b) for each human comment, identify which open question it answers or what new finding it introduces; (c) update the Open Questions section of `RESEARCH.md` — mark resolved questions with their answers, citing the comment date; (d) commit with `git commit -m "research: update with human feedback for #<N>"`; (e) comment on the PR summarising which questions were resolved; (f) STOP. If no human comments: continue with the existing first-run steps (steps 1–6 as currently defined).
- Output: `.github/agents/harness.md` with iteration-aware Research phase.
- Verification: `grep -n "iteration mode" .github/agents/harness.md | grep -i research` returns at least one match.
- Depends on: Step 1.1

### Phase 3 — Update Plan phase in `harness.md`

**Step 3.1 — Add iteration branch to the Plan phase procedure**
- Input: `.github/agents/harness.md` with Phase 2 changes applied
- Action: In the "Phase: Plan" section, prepend a Step 0:
  - Step 0: Run comment detection. If human comments are found AND `.tickets/ticket<N>/PLAN.md` already exists (iteration mode): (a) re-read `PLAN.md`; (b) for each human comment, identify the feedback it provides; (c) update `PLAN.md` to incorporate the feedback — add or modify steps as needed, appending a "Source: PR comment by <author> on <date>" note; (d) commit with `git commit -m "plan: update with human feedback for #<N>"`; (e) comment on the PR summarising changes made; (f) STOP. If no human comments OR `PLAN.md` does not exist yet: continue with the existing first-run steps (steps 1–5).
- Output: `.github/agents/harness.md` with iteration-aware Plan phase.
- Verification: `grep -n "iteration mode" .github/agents/harness.md | grep -i plan` returns at least one match.
- Depends on: Step 2.1

### Phase 4 — Update Implement phase in `harness.md`

**Step 4.1 — Add comment-reading step to the Implement phase procedure**
- Input: `.github/agents/harness.md` with Phase 3 changes applied
- Action: In the "Phase: Implement" section, add to "Step 0 — Validate prerequisites" (or insert a new Step 0 before the existing validate step):
  - Run comment detection. If human comments are found: read each comment and note any additional constraints, requirements, or clarifications they introduce. These must be incorporated when implementing the relevant plan steps. Cite each source in the commit message if a human comment directly influenced a change: `(per PR comment <date>)`.
  - If no human comments: proceed normally.
- Output: `.github/agents/harness.md` with comment-aware Implement phase.
- Verification: `grep -n "human comments" .github/agents/harness.md | grep -i implement` returns at least one match, OR the implement section contains the phrase "human comments".
- Depends on: Step 3.1

### Phase 5 — Update per-phase prompt files

**Step 5.1 — Update `research.prompt.md`**
- Input: `.github/prompts/research.prompt.md`
- Action: Add a new "## Iteration (re-invocation)" section after the existing "## Task" section. The section must mirror the iteration logic from Step 2.1: detect human comments using the agent-pattern approach; if found, update `RESEARCH.md` with answers and commit; if not, run the normal first-run task.
- Output: `.github/prompts/research.prompt.md` with iteration section.
- Verification: `grep -n "Iteration" .github/prompts/research.prompt.md` returns a match.
- Depends on: Step 2.1

**Step 5.2 — Update `plan.prompt.md`**
- Input: `.github/prompts/plan.prompt.md`
- Action: Add a new "## Iteration (re-invocation)" section after the existing "## Task" section, mirroring Step 3.1 logic.
- Output: `.github/prompts/plan.prompt.md` with iteration section.
- Verification: `grep -n "Iteration" .github/prompts/plan.prompt.md` returns a match.
- Depends on: Step 3.1

**Step 5.3 — Update `implement.prompt.md`**
- Input: `.github/prompts/implement.prompt.md`
- Action: In the "Step 0 — Validate prerequisites" section (or as a new Step 0), add: read PR comments using comment detection; if human comments exist, read them and note any constraints to incorporate during implementation. Mirror Step 4.1 logic.
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

- [ ] Step 1.1: `grep -n "Comment Detection" .github/agents/harness.md` returns a result
- [ ] Step 2.1: `grep -n "iteration mode" .github/agents/harness.md` returns a result in the Research section
- [ ] Step 3.1: `grep -n "iteration mode" .github/agents/harness.md` returns a result in the Plan section
- [ ] Step 4.1: The Implement section in `harness.md` contains the phrase "human comments"
- [ ] Step 5.1: `grep -n "Iteration" .github/prompts/research.prompt.md` returns a result
- [ ] Step 5.2: `grep -n "Iteration" .github/prompts/plan.prompt.md` returns a result
- [ ] Step 5.3: `grep -n "human comments\|PR comments" .github/prompts/implement.prompt.md` returns a result
- [ ] Step 6.1: `grep -n "PR comment" .github/instructions/plan.instructions.md` returns a result
- [ ] Step 6.2: `grep -n "re-invocation\|iteration" .github/instructions/research.instructions.md` returns a result

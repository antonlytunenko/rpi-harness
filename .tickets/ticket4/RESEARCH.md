# Research: Make harness iterate based on user comment

## Problem Analysis

The harness state machine is purely label-driven. When a phase is triggered (e.g., `agent-research`), the agent produces an artifact (`RESEARCH.md`, `PLAN.md`, or code), comments on the PR, and stops. There is **no mechanism** to detect or act on PR comments left by the human while the label remains unchanged.

This matters in two concrete scenarios:

1. **Research phase with open questions**: The agent writes `RESEARCH.md` including an "Open Questions" section and comments on the PR asking the human to answer them. The human answers in a PR comment but keeps the `agent-research` label, expecting the agent to update `RESEARCH.md`. The agent never re-reads the PR, so the open questions remain unanswered in the document and the plan phase cannot proceed safely.

2. **Plan phase with feedback**: The agent writes `PLAN.md` and stops. The human provides plan-level feedback in a PR comment (e.g., "Step 2.1 must also handle X") without changing the label. The agent never picks this up, so the feedback is lost.

3. **Implement phase with feedback**: Human leaves inline feedback or a PR comment during implementation without changing the label. The agent never re-reads and does not update the code.

The root cause is that in all three prompt files and in the agent definition, **no step reads PR comments**. The only signal the harness uses to decide what to do is the PR label.

### Current phase workflow (no comment-awareness)

**Research** (`.github/prompts/research.prompt.md`, lines 14–53, `.github/agents/harness.md` lines 42–56):
1. Read issue body
2. Explore codebase
3. Write `RESEARCH.md`
4. Commit + push
5. Comment on PR → STOP

**Plan** (`.github/prompts/plan.prompt.md`, lines 14–62, `.github/agents/harness.md` lines 58–72):
1. Read `RESEARCH.md`
2. Verify open questions resolved
3. Write `PLAN.md`
4. Commit + push
5. Comment on PR → STOP

**Implement** (`.github/prompts/implement.prompt.md`, lines 14–82, `.github/agents/harness.md` lines 74–116):
1. Read `PLAN.md`
2. Implement steps
3. Run tests (up to 3 iterations)
4. Commit + push, comment → STOP

None of these steps include reading PR comments.

### Available mechanism

`gh pr view --json comments` returns a `comments` array. Each element contains at minimum:
- `author` (with `login` sub-field) — identifies who posted the comment
- `body` — the comment text
- `createdAt` — timestamp

This is sufficient to:
- Filter comments by author (distinguish human vs. agent)
- Read all human comments before or after a phase artifact was last updated

## Affected Files

| File | Role | Observation |
|---|---|---|
| `.github/agents/harness.md` | Main agent definition — state machine orchestrator invoked by user | Contains per-phase procedures in full; no step reads PR comments; this is the primary entry point when the user runs the harness |
| `.github/prompts/research.prompt.md` | Research phase task specification | Lines 14–53: task steps read issue + codebase, but not PR comments; no iteration logic |
| `.github/prompts/plan.prompt.md` | Plan phase task specification | Lines 14–62: reads only `RESEARCH.md`; no step reads PR comments |
| `.github/prompts/implement.prompt.md` | Implement phase task specification | Lines 14–82: reads only `PLAN.md` + `RESEARCH.md`; no step reads PR comments |
| `.github/instructions/research.instructions.md` | Research phase behavioural constraints | Documents what agent must/must not do; no mention of comment iteration |
| `.github/instructions/plan.instructions.md` | Plan phase behavioural constraints | Documents plan constraints; no mention of comment iteration |
| `.github/instructions/implement.instructions.md` | Implement phase behavioural constraints | Documents implement constraints; no mention of comment iteration |

## Technical Constraints

- All harness behaviour is defined in Markdown files (`.md`). There is no runtime orchestrator script — `main.py` contains only a stub `print("Hello from rpi-harness!")` (line 2).
- The harness agent is a VS Code Copilot Agent (`model: claude-sonnet-4-5`, defined in `.github/agents/harness.md` lines 1–9). It is triggered manually by the user, not by a background poller.
- All GitHub interactions use the `gh` CLI. The command `gh pr view --json comments` is available and returns a `comments` array with `author.login`, `body`, and `createdAt` fields (confirmed by `gh pr view --json 2>&1`).
- The agent identifies itself by its GitHub login when it posts comments. Distinguishing agent comments from human comments requires comparing `author.login` to the agent's own login.
- The `.github/agents/harness.md` file is the authoritative source when the harness is invoked. The per-phase prompts (`.github/prompts/*.prompt.md`) are supplementary specifications; they must stay consistent with `harness.md`.
- Existing patterns (from `.tickets/ticket2/RESEARCH.md` and `.tickets/ticket2/PLAN.md`) show that prior changes to the harness have been purely to Markdown configuration files — no Python or shell orchestrator has been introduced.
- The `applyTo` selectors in instruction files affect when instructions are injected into context; changing them may affect instruction applicability.

## Open Questions

*All open questions resolved via investigation and codebase analysis on second invocation.*

### Resolved

1. **Agent identity for comment filtering** *(resolved)*: The harness uses the local `gh` CLI, which is authenticated with the repository owner's personal account (`antonlytunenko`). Consequently, **agent comments and human comments share the same `author.login`** — they cannot be distinguished by login alone. The reliable approach is **timestamp-based detection**: identify comments posted after the timestamp of the last agent comment for the current phase. Agent comments are also identifiable by their predictable content patterns (they always begin with "Research complete.", "Plan complete.", "Implementation complete.", "Cannot plan:", or contain "⚠️ Tests still failing"). Confirmed by inspecting `gh pr view 5 --json comments` output: agent comment shows `author.login: antonlytunenko`.

2. **Trigger for re-invocation** *(resolved)*: The harness is triggered manually by the user (`@harness` / "Run harness"). There is no automatic re-trigger mechanism, nor is one needed. When the user re-invokes the harness while the PR label has not changed, the harness must detect the presence of new human comments and iterate within the same phase rather than treating it as a first-run. This is confirmed by the current interaction: user re-invoked harness with `agent-research` still applied.

3. **Scope of "human comment"** *(resolved)*: Only comments posted **after the timestamp of the last agent comment in the current phase** should be treated as new iteration input. Pre-phase comments and prior-phase comments are not relevant. The cutoff timestamp is the `createdAt` of the most recent comment whose body matches a known agent comment pattern (see Q1 above). All comments after this cutoff are human comments.

4. **Implement-phase comment handling** *(resolved)*: The issue explicitly states "at any stage (research, plan or implement) harness does not take into account PR comments". All three phases must support iteration on human comments. In the implement phase, human comments may request code changes or provide additional context; the harness must read these before implementing each plan step on re-invocation.

5. **Conflict between comment feedback and phase constraints** *(resolved)*: When a human comment in the plan phase introduces a constraint not present in `RESEARCH.md`, the harness should incorporate it and cite its source (e.g., "Per PR comment by antonlytunenko on <date>"). The `plan.instructions.md` constraint "Every step must be grounded in a finding from RESEARCH.md" should be understood to include PR comment findings as valid sources — the spirit of the rule is traceability, not document exclusivity. If the new constraint is substantial, the harness should note in `PLAN.md` that the research phase should be revisited to document the finding formally.

# Implementation Summary: State-Machine Copilot Agent Harness

## Files Created

### `.github/agents/harness.md`
The main `@harness` chat participant definition. Contains:
- YAML front matter with `name`, `description`, `model: claude-sonnet-4-5`, and `tools` (`codebase`, `runCommands`, `readFile`, `editFiles`, `githubRepo`)
- Full state-machine system prompt encoding four phases: **Bootstrap**, **Research**, **Plan**, **Implement**
- Phase detection via `gh pr view --json labels`
- Bootstrap logic: creates branch, opens draft PR, applies `agent-research` label
- Research phase: explores codebase, writes `RESEARCH.md`, commits, comments on PR, stops
- Plan phase: reads `RESEARCH.md`, writes `PLAN.md`, commits, comments on PR, stops
- Implement phase: executes `PLAN.md` steps, writes code and tests, runs test suite in a max-3-iteration loop, comments green/red result, stops
- Hard boundaries section: never self-advance label, never merge PR, never push to `main`/`master`

### `.github/prompts/research.prompt.md`
Agent-mode prompt for the Research phase. Instructs the agent to:
- Read the linked GitHub issue
- Explore the codebase with `#codebase`
- Write `RESEARCH.md` with sections: Problem Analysis, Affected Files, Technical Constraints, Open Questions
- Commit, push, and comment on the PR
- Constraint: no implementation code, no source file changes other than `RESEARCH.md`

### `.github/prompts/plan.prompt.md`
Agent-mode prompt for the Plan phase. Instructs the agent to:
- Read `RESEARCH.md` (abort if missing or has unresolved open questions)
- Write `PLAN.md` with sections: Scope (Included/Excluded), Phases and Steps (each with Input/Action/Output/Verification/Dependencies), Dependency Graph, Verification Checklist
- Commit, push, and comment on the PR
- Constraint: no source code, every step grounded in `RESEARCH.md` findings

### `.github/prompts/implement.prompt.md`
Agent-mode prompt for the Implement phase. Instructs the agent to:
- Read `PLAN.md` and `RESEARCH.md`; detect test runner from `pyproject.toml` or `package.json`
- Implement each plan step in dependency order, with tests, referencing `(PLAN step N.M)` in commits
- Run the test suite after all steps; iterate up to 3 times on failures
- Green path: push, mark PR ready, comment success
- Red path (still failing after 3 cycles): commit `wip:` state, push, comment failure summary, stop

### `.github/instructions/research.instructions.md`
Scoped instruction file (`applyTo: RESEARCH.md`). Enforces:
- Document findings only — no implementation code, no concrete solutions
- Every claim must cite a file and line number
- Unknowns go to Open Questions, never assumed away

### `.github/instructions/plan.instructions.md`
Scoped instruction file (`applyTo: PLAN.md`). Enforces:
- Every step must reference a `RESEARCH.md` finding — no speculation beyond research scope
- No code of any kind inside `PLAN.md`
- Scope boundary (Included/Excluded) is mandatory
- Steps must be atomic, verifiable, and have explicit dependencies

### `.github/instructions/implement.instructions.md`
Scoped instruction file (`applyTo: **/*.{py,js,ts,go,rb}`). Enforces:
- Every change must trace to a `PLAN.md` step (referenced in commit message)
- Tests required for every new function and every bug fix
- Never skip the test run
- Minimal changes only — no unrequested refactoring
- `RESEARCH.md` and `PLAN.md` are read-only during this phase

## Runtime Flow

```
Human labels issue agent-ready
  → @harness bootstrap: creates branch + PR, applies agent-research
  → Research phase: RESEARCH.md committed, PR commented
Human changes label to agent-plan
  → @harness plan: PLAN.md committed, PR commented
Human changes label to agent-implement
  → @harness implement: code + tests written, test loop (≤3 iterations), PR commented
Human reviews and merges
```

## Deviations from PLAN.md

None. All seven files specified in the plan were created as described.

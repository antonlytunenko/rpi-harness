# Plan: State-Machine Copilot Agent Harness

## Architecture Overview

```
.github/
├── agents/
│   └── harness.md               ← custom @harness agent (state router + orchestrator)
├── prompts/
│   ├── research.prompt.md       ← task template: analyze codebase → RESEARCH.md
│   ├── plan.prompt.md           ← task template: read RESEARCH.md → PLAN.md
│   └── implement.prompt.md      ← task template: read PLAN.md → code + tests
└── instructions/
    ├── research.instructions.md ← scoped constraints when RESEARCH.md is active
    ├── plan.instructions.md     ← scoped constraints when PLAN.md is active
    └── implement.instructions.md ← scoped constraints when source files are active
```

---

## Steps

### Phase 1 — Core Agent Definition

**1. `.github/agents/harness.md`** — main `@harness` chat participant
- YAML front matter: `name`, `description`, `model`, `tools: [codebase, runCommands, readFile, editFiles, githubRepo]`
- System prompt encodes the full state machine: how to detect phase (`gh pr view --json labels`), what to do in each phase, hard boundaries (never self-advance a phase), and the implement-phase test feedback loop (max 3 iterations before stopping)

**2. `.github/prompts/research.prompt.md`** — research phase task
- Reads issue description, uses `#codebase` to explore affected areas, writes `RESEARCH.md` with: problem analysis, affected files, technical constraints, open questions
- Commits, comments on PR, tags issue creator for review

**3. `.github/prompts/plan.prompt.md`** — plan phase task
- Reads `RESEARCH.md`, produces `PLAN.md`: phases, step-by-step tasks with dependencies, verification steps, explicit scope boundary (included/excluded)
- Commits, comments on PR, tags human for approval

**4. `.github/prompts/implement.prompt.md`** — implement phase task
- Reads `PLAN.md`, writes code + tests following each plan step
- Runs `pytest` / `npm test` via terminal; if failures → re-reads errors, iterates up to 3 times
- Tags human **only** when tests are green; if still failing after 3 cycles → comments with failure summary and stops

### Phase 2 — Scoped Instruction Files

**5. `.github/instructions/research.instructions.md`**
- `applyTo: RESEARCH.md`
- Constraints: "document findings only — no implementation code, no concrete solutions"

**6. `.github/instructions/plan.instructions.md`**
- `applyTo: PLAN.md`
- Constraints: "produce a plan referencing RESEARCH.md findings — no code, no speculation beyond research scope"

**7. `.github/instructions/implement.instructions.md`**
- `applyTo: **/*.{py,js,ts,go,rb}`
- Constraints: "every change must trace to a PLAN.md step — tests required for every new function, never skip the test run"

---

## Runtime Flow

1. Human labels issue `agent-ready` on GitHub
2. Human opens VS Code Copilot Chat → selects `@harness`
3. Agent runs `gh issue list --label agent-ready`, creates branch + PR, applies label `agent-research`, starts research via `#research` prompt
4. Human reviews `RESEARCH.md` → changes label to `agent-plan`
5. Human invokes `@harness` → agent detects `agent-plan` → generates `PLAN.md`
6. Human reviews → changes label to `agent-implement`
7. Human invokes `@harness` → agent generates code + tests, iterates on failures, tags human when green

**Hard boundary**: phases never self-advance. Each transition requires a human label change.

---

## Decisions

- **No Python/polling**: state transitions are human-gated (label changes); agent is invoked on-demand in VS Code Chat
- **Reusable template**: all files live under `.github/`, copy them to any repo to get the harness
- **Skills = built-in VS Code tools** (`runCommands` for `gh`/`pytest`, `editFiles` for writing outputs) — no custom server needed
- **Phase isolation**: instruction files automatically inject constraints based on which file type is in context

---

## Verification

1. Open VS Code Copilot Chat — `@harness` appears as a selectable agent
2. Create a test issue labeled `agent-ready` → invoke `@harness` → verify branch + PR created + `agent-research` label applied
3. Verify `RESEARCH.md` committed and PR commented
4. Manually change label to `agent-plan` → invoke `@harness` → verify `PLAN.md` produced
5. Manually change label to `agent-implement` → introduce a deliberate test failure → verify agent iterates before tagging human

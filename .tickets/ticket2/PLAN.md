# Plan: Improve harness integrity

## Scope

### Included

- Fix file path conflicts in `.github/agents/harness.md`: Research and Plan phase sections reference `RESEARCH.md` and `PLAN.md` at repo root, but the canonical location is `.tickets/ticket<issue_number>/RESEARCH.md` and `.tickets/ticket<issue_number>/PLAN.md`
- Fix `applyTo` selectors in `research.instructions.md` and `plan.instructions.md` to match the canonical `.tickets/ticket*/RESEARCH.md` and `.tickets/ticket*/PLAN.md` paths
- Fix "do not modify" path references in `plan.instructions.md` and `implement.instructions.md` to specify canonical paths
- Fix the internal inconsistency in the Inputs section of `implement.prompt.md` (lines referencing root-level `PLAN.md` and `RESEARCH.md` that conflict with lines 16–17 referencing `.tickets/ticket<issue_number>/` paths)

### Excluded

- Removing or restructuring the full phase procedure sections in `.github/agents/harness.md` (Open Question 2 — structural change requiring human decision)
- Moving Hard Boundaries to a dedicated shared file (Open Question 3 — deferred)
- Changes to `research.prompt.md` or `plan.prompt.md` (these are internally consistent and use the correct canonical paths)
- Any changes to source code files, tests, or non-Markdown configuration

## Phases and Steps

### Phase 1 — Fix file path conflicts in `harness.md`

**Step 1.1 — Update Research phase file reference in `harness.md`**
- Input: `.github/agents/harness.md` — Research phase section that instructs writing `RESEARCH.md` in the repo root and running `git add RESEARCH.md`
- Action: Change the write instruction from "Write `RESEARCH.md` in the repo root" to "Write `.tickets/ticket<issue_number>/RESEARCH.md`", and update the `git add` command from `git add RESEARCH.md` to `git add .tickets/ticket<issue_number>/RESEARCH.md`
- Output: `.github/agents/harness.md` with corrected file path in Research phase section
- Verification: `grep -n 'tickets' .github/agents/harness.md | grep RESEARCH` returns at least one match
- Depends on: none

**Step 1.2 — Update Plan phase file reference in `harness.md`**
- Input: `.github/agents/harness.md` — Plan phase section that instructs writing `PLAN.md` in the repo root and running `git add PLAN.md`
- Action: Change the write instruction from "Write `PLAN.md` in the repo root" to "Write `.tickets/ticket<issue_number>/PLAN.md`", and update the `git add` command from `git add PLAN.md` to `git add .tickets/ticket<issue_number>/PLAN.md`
- Output: `.github/agents/harness.md` with corrected file path in Plan phase section
- Verification: `grep -n 'tickets' .github/agents/harness.md | grep PLAN` returns at least one match
- Depends on: none

### Phase 2 — Fix `applyTo` selectors in instruction files

**Step 2.1 — Update `applyTo` selector in `research.instructions.md`**
- Input: `.github/instructions/research.instructions.md` — front matter with `applyTo: RESEARCH.md`
- Action: Change `applyTo` value from `RESEARCH.md` to `.tickets/ticket*/RESEARCH.md`
- Output: `.github/instructions/research.instructions.md` with corrected `applyTo` selector
- Verification: `head -3 .github/instructions/research.instructions.md | grep '.tickets/ticket\*/RESEARCH.md'` returns a match
- Depends on: none

**Step 2.2 — Update `applyTo` selector in `plan.instructions.md`**
- Input: `.github/instructions/plan.instructions.md` — front matter with `applyTo: PLAN.md`
- Action: Change `applyTo` value from `PLAN.md` to `.tickets/ticket*/PLAN.md`
- Output: `.github/instructions/plan.instructions.md` with corrected `applyTo` selector
- Verification: `head -3 .github/instructions/plan.instructions.md | grep '.tickets/ticket\*/PLAN.md'` returns a match
- Depends on: none

### Phase 3 — Fix "do not modify" path references in instruction files

**Step 3.1 — Update path reference in `plan.instructions.md`**
- Input: `.github/instructions/plan.instructions.md` — last rule: "Do not modify RESEARCH.md" (no path qualification)
- Action: Change the rule text to specify the canonical path: "Do not modify `.tickets/ticket<issue_number>/RESEARCH.md`"
- Output: `.github/instructions/plan.instructions.md` with qualified path in the "do not modify" rule
- Verification: `grep 'tickets' .github/instructions/plan.instructions.md | grep RESEARCH` returns a match
- Depends on: Step 2.2

**Step 3.2 — Update path references in `implement.instructions.md`**
- Input: `.github/instructions/implement.instructions.md` — rule: "Do not modify RESEARCH.md or PLAN.md" (no path qualification)
- Action: Change the rule text to specify canonical paths: "Do not modify `.tickets/ticket<issue_number>/RESEARCH.md` or `.tickets/ticket<issue_number>/PLAN.md`"
- Output: `.github/instructions/implement.instructions.md` with qualified paths in the "do not modify" rule
- Verification: `grep 'tickets' .github/instructions/implement.instructions.md | grep PLAN` returns a match
- Depends on: none

### Phase 4 — Fix internal inconsistency in `implement.prompt.md`

**Step 4.1 — Fix Inputs section paths in `implement.prompt.md`**
- Input: `.github/prompts/implement.prompt.md` — Inputs section listing `PLAN.md` and `RESEARCH.md` at repo root (conflicting with lines 16–17 which correctly reference `.tickets/ticket<issue_number>/PLAN.md` and `.tickets/ticket<issue_number>/RESEARCH.md`)
- Action: Change the Inputs section entries from root-level `PLAN.md` and `RESEARCH.md` to `.tickets/ticket<issue_number>/PLAN.md` and `.tickets/ticket<issue_number>/RESEARCH.md`
- Output: `.github/prompts/implement.prompt.md` with a consistent file path throughout
- Verification: `grep -A4 '## Inputs' .github/prompts/implement.prompt.md | grep 'tickets'` returns at least two matches
- Depends on: none

## Dependency Graph

1. Step 1.1 — Update Research phase file reference in `harness.md`
2. Step 1.2 — Update Plan phase file reference in `harness.md`
3. Step 2.1 — Update `applyTo` selector in `research.instructions.md`
4. Step 2.2 — Update `applyTo` selector in `plan.instructions.md`
5. Step 3.1 — Update path reference in `plan.instructions.md` (depends on Step 2.2)
6. Step 3.2 — Update path references in `implement.instructions.md`
7. Step 4.1 — Fix Inputs section paths in `implement.prompt.md`

Steps 1.1, 1.2, 2.1, 2.2, 3.2, and 4.1 are independent and may execute in any order. Step 3.1 must execute after Step 2.2.

## Verification Checklist

- [ ] Step 1.1: `grep -n 'tickets' .github/agents/harness.md | grep RESEARCH` returns at least one match
- [ ] Step 1.2: `grep -n 'tickets' .github/agents/harness.md | grep PLAN` returns at least one match
- [ ] Step 2.1: `head -3 .github/instructions/research.instructions.md` shows `applyTo: .tickets/ticket*/RESEARCH.md`
- [ ] Step 2.2: `head -3 .github/instructions/plan.instructions.md` shows `applyTo: .tickets/ticket*/PLAN.md`
- [ ] Step 3.1: `grep 'tickets' .github/instructions/plan.instructions.md | grep RESEARCH` returns a match
- [ ] Step 3.2: `grep 'tickets' .github/instructions/implement.instructions.md | grep PLAN` returns a match
- [ ] Step 4.1: `grep -A4 '## Inputs' .github/prompts/implement.prompt.md | grep 'tickets'` returns at least two matches

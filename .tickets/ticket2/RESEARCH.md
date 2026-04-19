# Research: Improve harness integrity

## Problem Analysis

The harness system consists of three layers: an agent file (`harness.md`), instruction files (per phase), and prompt files (per phase). Currently the agent file and the prompt files duplicate the same git/gh commands and workflow steps, creating conflicting or inconsistent sources of truth.

**Specific duplications observed:**

1. **Bootstrap / Research phase git+gh commands** appear in both:
   - `.github/agents/harness.md` lines 45–52 (commit `RESEARCH.md`, `gh pr comment`)
   - `.github/prompts/research.prompt.md` lines 44–57 (commit `.tickets/ticket<N>/RESEARCH.md`, `gh pr comment`)

2. **Plan phase git+gh commands** appear in both:
   - `.github/agents/harness.md` lines 67–73 (commit `PLAN.md`, `gh pr comment`)
   - `.github/prompts/plan.prompt.md` lines 54–63 (commit `.tickets/ticket<N>/PLAN.md`, `gh pr comment`)

3. **Implement phase test loop and final comments** appear in both:
   - `.github/agents/harness.md` lines 78–116 (full loop, both green and red path comments)
   - `.github/prompts/implement.prompt.md` lines 35–82 (same loop, same comments)

4. **Hard boundaries** (never merge, never push to main, etc.) appear in:
   - `.github/agents/harness.md` lines 120–126
   - `.github/instructions/implement.instructions.md` lines 15–17 (partial overlap)

**Conflicting statements observed:**

1. **File location inconsistency for RESEARCH.md and PLAN.md:**
   - `.github/agents/harness.md` line 49 references `RESEARCH.md` (repo root)
   - `.github/prompts/research.prompt.md` line 35 references `.tickets/ticket<issue_number>/RESEARCH.md`
   - `.github/agents/harness.md` line 68 references `PLAN.md` (repo root)
   - `.github/prompts/plan.prompt.md` line 43 references `.tickets/ticket<issue_number>/PLAN.md`
   - `.github/instructions/plan.instructions.md` line 17 says "Do not modify RESEARCH.md" without specifying path
   - `.github/instructions/implement.instructions.md` line 14 says "Do not modify RESEARCH.md or PLAN.md" without specifying path

2. **`applyTo` selectors in instruction files do not match the actual files they guard:**
   - `.github/instructions/research.instructions.md` line 2: `applyTo: RESEARCH.md` — but the canonical file is `.tickets/ticket<N>/RESEARCH.md`
   - `.github/instructions/plan.instructions.md` line 2: `applyTo: PLAN.md` — but the canonical file is `.tickets/ticket<N>/PLAN.md`
   - `.github/instructions/implement.instructions.md` line 2: `applyTo: "**/*.{py,js,ts,go,rb}"` — this is correct for source files, but the "do not modify RESEARCH.md/PLAN.md" rules in this file refer to files with different paths than the selector implies

3. **Implement prompt references wrong file paths:**
   - `.github/prompts/implement.prompt.md` lines 9–10 reference `PLAN.md` and `RESEARCH.md` (root) in the "Inputs" section
   - But lines 16, 17, 22 reference `.tickets/ticket<issue_number>/PLAN.md` and `.tickets/ticket<issue_number>/RESEARCH.md`

**Role overlap between agent and prompts:**

- `.github/agents/harness.md` currently defines:
  - Phase detection logic (lines 17–26) ✓ appropriate for agent
  - Bootstrap steps (lines 32–40) — partially appropriate, but includes detail that overlaps prompts
  - Full Research phase procedure (lines 42–56) — duplicates `research.prompt.md`
  - Full Plan phase procedure (lines 58–72) — duplicates `plan.prompt.md`
  - Full Implement phase procedure (lines 74–116) — duplicates `implement.prompt.md`
  - Hard Boundaries (lines 118–126) — duplicates parts of `implement.instructions.md`

- The prompts (`research.prompt.md`, `plan.prompt.md`, `implement.prompt.md`) are designed to be the detailed, authoritative source for each phase, but the agent file re-specifies the same procedures without referring to these files.

## Affected Files

| File | Role | Observation |
|---|---|---|
| `.github/agents/harness.md` | Agent definition — state machine orchestrator | Contains full phase procedures duplicating the prompts; should only contain workflow/orchestration logic and delegate to prompts/instructions for detail |
| `.github/prompts/research.prompt.md` | Research phase detailed task specification | Contains the canonical git/gh commands for research; uses `.tickets/ticket<N>/RESEARCH.md` path |
| `.github/prompts/plan.prompt.md` | Plan phase detailed task specification | Contains the canonical git/gh commands for plan; uses `.tickets/ticket<N>/PLAN.md` path |
| `.github/prompts/implement.prompt.md` | Implement phase detailed task specification | Contains the canonical test loop and final comments; has minor internal inconsistency (root vs ticket path in Inputs section) |
| `.github/instructions/research.instructions.md` | Research phase behavioural constraints | `applyTo: RESEARCH.md` selector does not match canonical path `.tickets/ticket<N>/RESEARCH.md` |
| `.github/instructions/plan.instructions.md` | Plan phase behavioural constraints | `applyTo: PLAN.md` selector does not match canonical path `.tickets/ticket<N>/PLAN.md` |
| `.github/instructions/implement.instructions.md` | Implement phase behavioural constraints | `applyTo` covers source files correctly; "do not modify" rules reference ambiguous file paths |

## Technical Constraints

- All files are Markdown with YAML front matter.
- `.github/agents/harness.md` front matter (lines 1–9) specifies `model: claude-sonnet-4-5`, `tools`, and metadata — this must be preserved.
- `.github/prompts/*.prompt.md` front matter specifies `mode: agent`, `description`, and `tools` — must be preserved.
- `.github/instructions/*.instructions.md` front matter specifies `applyTo` glob — changing the `applyTo` value changes which files trigger the instruction.
- No source code files (`.py`, `.js`, etc.) are involved; all changes are to Markdown configuration files.
- The `.tickets/` directory structure (`.tickets/ticket<N>/RESEARCH.md`, `.tickets/ticket<N>/PLAN.md`) is the pattern established by the prompts and used in `.tickets/init/`.

## Open Questions

1. Should the `applyTo` selectors in `research.instructions.md` and `plan.instructions.md` be updated to match the `.tickets/ticket*/RESEARCH.md` and `.tickets/ticket*/PLAN.md` paths, or should those instruction files be restructured to apply more broadly?
2. Should `.github/agents/harness.md` explicitly reference the prompt files by name (e.g., "invoke the research prompt") or only describe the phase at a high level and trust the prompt files to be loaded separately?
3. Should "Hard Boundaries" remain only in `harness.md`, only in `implement.instructions.md`, or in a dedicated shared constraints file?

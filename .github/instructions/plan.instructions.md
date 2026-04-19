---
applyTo: PLAN.md
---

# Plan Phase Constraints

These rules apply whenever `PLAN.md` is the active file in context.

- **Reference RESEARCH.md findings.** Every step must be grounded in a finding from `RESEARCH.md`. Do not introduce steps that address problems not documented there.
- **No code.** Do not write source code, test code, configuration snippets, or pseudocode inside `PLAN.md`.
- **No speculation.** Do not plan for edge cases, future features, or scenarios not identified in the research phase.
- **Explicit scope boundary required.** The Included and Excluded sections must be present and non-empty.
- **Steps must be atomic and verifiable.** Each step must have a single clear output and a verification command or observable outcome.
- **Dependencies must be explicit.** If a step depends on another, state it — do not rely on the reader to infer ordering.
- **Do not modify RESEARCH.md.** Read it; do not edit it.

---
applyTo: .tickets/ticket*/RESEARCH.md
---

# Research Phase Constraints

These rules apply whenever `RESEARCH.md` is the active file in context.

- **Document findings only.** Record what you observe in the codebase. Do not propose solutions, architectures, or implementation approaches.
- **No implementation code.** Do not write, suggest, or include any source code, pseudocode, or concrete fix snippets.
- **No concrete solutions.** Identifying a problem is correct; prescribing a solution is not permitted in this phase.
- **Cite sources.** Every claim about the codebase must reference a specific file and line number.
- **Flag unknowns.** If anything is ambiguous or unclear, add it to the Open Questions section rather than assuming.
- **Scope conservatively.** When uncertain whether a file is affected, list it with a note rather than excluding it.
- **On re-invocation (iteration mode), PR comments that answer open questions are valid findings.** Incorporate the answer into `RESEARCH.md`, cite the comment author and date, and mark the question as resolved.

# Plan: Ignore Closed PR (Issue #14)

## Phases

### Phase 1 — Update harness agent instructions

**Input:** `.github/agents/harness.md`  
**Output:** Same file, with "no PR exists yet" replaced by an "no **open** PR linked to the issue" rule and a collision strategy for branch naming.

#### Steps

**Step 1.1 — Fix the state-machine detection sentence**

Locate line 35 (How to detect the current phase section):

> `If no PR exists yet and the issue has label `agent-ready`, create the branch, PR, and apply `agent-research`.`

Replace with:

> `If the issue has label `agent-ready` and no **open** PR is linked to it (checked via explicit linked-issue metadata: `gh pr list --json number,title,state,closingIssuesReferences --jq '…'`), create the branch, PR, and apply `agent-research`. If a closed PR exists but no open one, treat the issue as restartable and proceed with bootstrap. If an open PR already exists, skip bootstrap.`

**Step 1.2 — Update the Bootstrap phase steps**

Add a pre-check step at the top of the Phase: Bootstrap section:

```
0. Guard — check for an existing open PR linked to the issue:
   gh pr list --state open --json number,closingIssuesReferences \
     --jq ".[] | select(.closingIssuesReferences[].number == <issue_number>)"
   If any result is returned, STOP — do not create a branch or PR.
```

**Step 1.3 — Define branch collision strategy**

Add a new sub-section "Branch naming on restart" inside Phase: Bootstrap:

```
### Branch naming on restart

If `git checkout -b issue-<number>/<slug>` fails because the branch already exists
(closed-PR scenario), append a numeric suffix:

  issue-<number>/<slug>-2
  issue-<number>/<slug>-3
  …

Try up to suffix `-9`; if all are taken, abort with an error message.
```

**Verification:** `grep -n "open PR\|restart\|suffix" .github/agents/harness.md` returns the new lines.

---

### Phase 2 — Update the product spec

**Input:** `.specs/harness-spec-001.md`  
**Output:** Same file, with the trigger line corrected to "No **open** PR linked to the issue exists".

#### Steps

**Step 2.1 — Fix the trigger description**

Locate:

> `* **Trigger:** Issue labeled `agent-ready` + No PR exists → Create Branch/PR → Label `agent-research`.`

Replace with:

> `* **Trigger:** Issue labeled `agent-ready` + No **open** PR linked to the issue (by explicit linked-issue metadata) → Create Branch/PR → Label `agent-research`. Closed historical PRs do not block restart.`

**Verification:** `grep "Trigger" .specs/harness-spec-001.md` shows the updated line.

---

## Dependencies

- Step 1.2 and 1.3 must follow Step 1.1 (all edits are in the same file; apply in order).
- Phase 2 is independent of Phase 1 and can be done in any order.

---

## Verification (end-to-end)

```
grep -n "open PR\|restart\|suffix\|collision" .github/agents/harness.md
grep -n "open PR\|Closed\|linked-issue" .specs/harness-spec-001.md
```

Both commands must return non-empty output after the edits.

---

## Scope Boundary

**Included:**
- Wording changes in `.github/agents/harness.md` (state-machine intro, Bootstrap phase guard, branch collision strategy).
- Wording changes in `.specs/harness-spec-001.md` (trigger description).

**Excluded:**
- Any changes to Python source files (`main.py`, `harness/scanner.py`, etc.).
- Runtime enforcement of the "ignore closed PR" rule in code.
- Changes to any other documentation or configuration files.

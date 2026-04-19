# **Project Goal: State-Machine Agentic Harness**
**Objective:** Build a local Python orchestrator that manages a Research-Plan-Implement loop for an AI agent using GitHub Issues and PRs as the interface.

## **1. Core Logic (The State Machine)**
The script must poll the GitHub CLI (`gh`) and move tasks through these states based on **PR Labels**:
* **Trigger:** Issue labeled `agent-ready` + No PR exists → Create Branch/PR → Label `agent-research`.
* **State: `agent-research`** * **Action:** Agent analyzes the codebase and generates `RESEARCH.md`.
    * **Harness Sensor:** Tags the Issue creator for review.
* **State: `agent-plan`** (Triggered by Human label change)
    * **Action:** Agent reads `RESEARCH.md` and generates a detailed `PLAN.md`.
    * **Harness Sensor:** Tags Human for approval.
* **State: `agent-implement`** (Triggered by Human label change)
    * **Action:** Agent writes code and tests.
    * **Harness Sensor:** Runs local test suite (`pytest`/`npm test`). Only pushes and tags Human if tests pass.

## **2. Technical Requirements**
* **Interface:** Use the GitHub CLI (`gh`) for all interactions (labels, comments, PR creation).
* **AI Integration:** Use `gh copilot` commands or the Copilot API to generate content for each phase.
* **Context Management:** Each phase must be "Harnessed" by a specific system prompt (e.g., "In Research phase, do not write implementation code").
* **Loop:** The script should run as a local background process (polling every 5 minutes).

## **3. Engineering Constraints (The "Harness")**
* **Stiff Boundaries:** The agent cannot progress to the next label/state without Human approval (label change).
* **Feedback Loops:** If local "Sensors" (tests/linters) fail during the implementation phase, the orchestrator must feed the error back to the agent for auto-correction before the Human sees the PR.
# rpi-harness

A polling agent harness that monitors GitHub repositories for issues and pull requests labelled with `agent-research`, `agent-plan`, or `agent-implement`, and automatically invokes the GitHub Copilot CLI (`gh copilot suggest`) to drive each item through the corresponding workflow phase.

## How it works

1. **Read** a list of GitHub repository URLs from `repositories.txt` (one URL per line, comments start with `#`).
2. **Scan** each repository for issues and PRs that carry any of the agent phase labels using the `gh` CLI.
3. **Deduplicate** — only items with new activity since the last poll are processed, tracked in `<work-dir>/.harness_state.json`.
4. **Provision** a temporary workspace: clone the target repo and copy the harness `.github/` directory tree into it.
5. **Invoke** `gh copilot suggest` with a prompt describing the item; the agent runs the appropriate phase.
6. **Sleep** for the configured interval and repeat.

## Prerequisites

- Python 3.11+
- [`gh` CLI](https://cli.github.com/) authenticated (`gh auth login`)
- `git` available on `PATH`

## Installation

```bash
git clone https://github.com/antonlytunenko/rpi-harness.git
cd rpi-harness
pip install -e .
# or, with dev dependencies (includes pytest):
pip install -e ".[dev]"
```

## Configuration

### `repositories.txt`

List the GitHub repositories to monitor, one full URL per line:

```
# repositories.txt
https://github.com/owner/my-project
https://github.com/another-org/another-repo
```

Blank lines and lines starting with `#` are ignored.

## Usage

```
python main.py --work-dir <path> [--repos-file <path>] [--interval <seconds>]
```

### Arguments

| Argument | Default | Description |
|---|---|---|
| `--work-dir` | *(required)* | Directory under which temporary workspaces are created |
| `--repos-file` | `repositories.txt` | Path to the file listing repository URLs |
| `--interval` | `300` | Poll interval in seconds |

### Examples

**Run with default settings (polls every 5 minutes):**

```bash
python main.py --work-dir /tmp/harness-work
```

**Use a custom repositories file and poll every 2 minutes:**

```bash
python main.py --work-dir /tmp/harness-work \
               --repos-file /etc/harness/repos.txt \
               --interval 120
```

**Dry-run style one-shot check (interval irrelevant for a single pass, but you can interrupt after the first cycle):**

```bash
python main.py --work-dir /tmp/harness-work --interval 999999
# Ctrl-C after the first poll cycle completes
```

**Show help:**

```bash
python main.py --help
```

## Running tests

```bash
pytest -q
```

## Project layout

```
rpi-harness/
├── main.py               # Polling entry-point
├── repositories.txt      # Repos to monitor (edit this)
├── harness/
│   ├── scanner.py        # Read repo list; find labelled issues/PRs via gh CLI
│   ├── dedup.py          # State tracking to skip already-processed items
│   ├── workspace.py      # Clone repo and inject harness .github/ directory
│   └── runner.py         # Invoke gh copilot suggest in the cloned workspace
└── tests/                # pytest unit tests for each module
```

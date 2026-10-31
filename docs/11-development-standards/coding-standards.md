# Coding standards

| Field | Value |
|---|---|
| Purpose | How code is written in this project |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Project structure](../11-development-standards/project-structure.md), [Code review](../11-development-standards/code-review.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

These are the owner's approved rules, copied word for word from WORK_PLAN.md section 5. Ruff and mypy in CI (step 1.4) enforce style and types from Phase 1. All other rules are working rules and are not enforced by tooling.

### 5.1 Project rules

| ID | Rule |
|---|---|
| Z | Zero cost. Public GitHub repo, standard runners only. No new payment method or paid plan for this project on GitHub, Hugging Face, Kaggle or Google. The owner's existing 2 TB Google Drive is used as it is. No paid tiers, no trials, no Colab compute units |
| P | One phase at a time. No code until "start Phase X". After each phase: check results, fix problems, show a done/not-done table, then ask before the next phase |
| S | End every step with what to do next |
| G | Commit and push after every step. Merge to main at phase end with a version tag. Update CHANGELOG.md and this file every step |
| L | Every push to main that passes CI rebuilds the dashboard and the demo automatically |
| A | Each feature phase adds its API endpoint and its demo feature together with the feature |
| V | Private documents never go to Colab, Kaggle, GitHub, Google Drive, the dashboard or the demo |
| E | Evaluations run in the Mac profile and, where useful, the GPU profile. Logged in MLflow and exported to the repo |
| H | Never guess. If unsure, say so and check. When something fails, find the real cause |
| T | Every technology must have a real purpose |
| N | Never claim production-ready, real-time, automated or accurate unless implemented and verified |
| K | Keep this project's chats separate from the thesis and presentation work. Do not teach the Hugging Face course |

### 5.2 Communication and coding rules

| ID | Rule |
|---|---|
| C1 | Very easy English, step by step, with why each step is needed |
| C2 | Flat modules in src/mrag/. Run with uv run python -m mrag.<module> |
| C3 | Code files are written by the coding assistant in the project folder, only after the owner approves each change. Never through terminal commands such as heredoc |
| C4 | Give a short hash check for every code file plus the Mac command to compute it |
| C5 | Write every command in full. Never say "the command from step X". Group independent commands |
| C6 | Git commands one per line (git add, git commit -m "...", git push), never chained with &&. Write the expected output under them. You only send output if it differs |
| C7 | Plain human code style with useful comments. No AI-looking formatting, no emojis, no long docstrings |
| C8 | Never put a comma directly before "and", "or" or "but" |
| C9 | Notebook instructions: label every cell with a descriptive name (plus Markdown or Code) |
| C10 | Steps use numbered sub-steps (for example 0.1.1, 0.1.2), each command block followed by a short Why |
| C11 | Do not create files (README, docs, images) unless asked. Planned docs in this plan count as asked when their step starts |
| C12 | Verification loop. For every step the coding assistant gives the code, the exact commands and the expected output, including the verification number of each Python code file. You run the commands with uv and compare. Everything matches: the step is done and you send nothing. Anything differs: you send only the different output. The coding assistant finds the real cause and gives the fix with new expected output. When an output can't be predicted exactly (for example real training results or live data), the coding assistant says so and you send that output before committing |
| C13 | Verification number: the first 12 characters of the SHA-256 of the file's Python syntax tree, `ast.dump(ast.parse(...))`. Comments and formatting do not change it. You run one inline command that lists the files: `uv run python -c "import ast, hashlib ..."` |
| C14 | No product comparisons such as "ChatGPT-style" or "NotebookLM-style" in any file in the repo (code, docs, README, commit messages). Describe what the feature does instead. The owner used such words in planning only to explain ideas |

Error handling, logging and type rules beyond ruff and mypy: REQUIRES CONFIRMATION when code starts.

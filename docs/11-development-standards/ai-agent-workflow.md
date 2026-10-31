# AI agent workflow

| Field | Value |
|---|---|
| Purpose | Instructions for AI assistants working on this project |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [WORK_PLAN handover](../WORK_PLAN.md), [Definition of done](../11-development-standards/definition-of-done.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

## Rules for any AI assistant

1. WORK_PLAN.md is the single source of truth. Read it fully before acting.
2. Follow every rule in WORK_PLAN.md section 5.
3. Never invent completed work. Check claims against the git log and file list.
4. Never change a decision without explaining why and asking the owner.
5. One phase at a time. Start only after "start Phase X".
6. Never claim production-ready, real-time, automated or accurate without verification.
7. Use the verification loop for every step (WORK_PLAN.md rules C12 and C13).

## Handover

Follow the checklist in [WORK_PLAN.md](../WORK_PLAN.md), section 15.1.

### 15.1 End-of-chat checklist (do this before leaving every chat)

1. Finish the current step completely or roll it back. Never leave a step half done.
2. Update this file: step status, Current State table (section 1), decision log (4.1), open questions (4.2).
2a. Update docs/HANDOVER.md: files changed, test results, problems and fixes, deviations from the plan and the exact next step.
3. Commit and push (git add, git commit -m "...", git push). Merge and tag if a phase ended.
4. Check that CI is green and the dashboard shows the new status.
5. Run make backup.
6. Download docs/WORK_PLAN.md from GitHub for the next chat.

## Change requests (PROPOSED, not yet in WORK_PLAN.md)

```
CHANGE REQUEST for WORK_PLAN.md
Change: [what changes]
Reason: [who decided and when]
Rules:
1. Apply the change everywhere it matters.
2. Change nothing else.
3. Add a decision-log row and update the current plan version.
4. List every place changed.
5. Return the updated WORK_PLAN.md and WORK_PLAN.docx.
```


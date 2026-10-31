# Definition of done

| Field | Value |
|---|---|
| Purpose | When a step and a phase count as done |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Acceptance criteria](../01-requirements/acceptance-criteria.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

## A step is done when

1. Its done-when test passed and the result is recorded.
2. Code has hash checks (C4) and is committed and pushed.
2a. Your terminal output and verification numbers match the coding assistant's expected output (rules C12, C13).
3. CI is green.
4. WORK_PLAN.md Current State and step status are updated.
5. The answer ends with what to do next (rule S).

## A phase is done when

1. All its steps are done.
2. A done/not-done table is shown.
3. The branch is merged by pull request and tagged.
4. Dashboard and demo show the update.
5. The owner gives permission for the next phase (rule P).

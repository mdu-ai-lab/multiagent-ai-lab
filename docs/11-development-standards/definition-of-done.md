# Definition of done

| Field | Value |
|---|---|
| Purpose | When a step and a phase count as done |
| Status | Proposed |
| Last updated | 2026-11-05 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Acceptance criteria](../01-requirements/acceptance-criteria.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

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

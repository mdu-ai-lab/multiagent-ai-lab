# Code review

| Field | Value |
|---|---|
| Purpose | Proposed pull request checklist |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Definition of done](../11-development-standards/definition-of-done.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

PROPOSED checklist for every pull request:

1. CI is green (lint, types, tests, scans, eval gate).
2. The step's done-when test passed and the result is recorded.
3. No private data, secrets or large files in the diff.
4. Coding rules C2 to C9 followed.
7. Verification numbers of all changed Python files match (rules C12, C13).
5. WORK_PLAN.md status and CHANGELOG.md updated.
6. New endpoints added to the endpoint catalog (rule A).

Required number of reviewers: REQUIRES CONFIRMATION (depends on group size and Q8).

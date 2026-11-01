# Testing status

| Field | Value |
|---|---|
| Purpose | What has actually been tested |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Test plan](../09-testing/test-plan.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Category | Count |
|---|---|
| Tests that exist | 24 |
| Tests inspected | 24 |
| Tests executed | 24 |
| Tests passed | 24 |
| Tests failed | 0 |
| Tests missing | All other planned tests (see test plan) |

Reason: 24 tests for the model client: 14 unit tests, 7 integration tests with the Mac model server and 3 with the transformers backend. Steps 0.1 to 0.5 were also checked with the verification loop (rules C12, C13), see docs/HANDOVER.md. CI comes in step 1.4. Update this file at the end of every step.

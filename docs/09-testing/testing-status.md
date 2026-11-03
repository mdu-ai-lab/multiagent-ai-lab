# Testing status

| Field | Value |
|---|---|
| Purpose | What has actually been tested |
| Status | Proposed |
| Last updated | 2026-11-03 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Test plan](../09-testing/test-plan.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Category | Count |
|---|---|
| Tests that exist | 39 |
| Tests inspected | 39 |
| Tests executed | 39 |
| Tests passed | 39 |
| Tests failed | 0 |
| Tests missing | All other planned tests (see test plan) |

Reason: 39 tests: 29 unit tests (14 for the model client, 15 for the backup), 7 integration tests with the Mac model server and 3 with the transformers backend. The 29 unit tests last ran on 3 November 2026. The 10 integration tests need a running model server or the demo packages and last ran on 1 November 2026. Steps 0.1 to 0.6 were also checked with the verification loop (rules C12, C13), see docs/HANDOVER.md. CI comes in step 1.4. Update this file at the end of every step.

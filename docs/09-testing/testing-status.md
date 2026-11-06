# Testing status

| Field | Value |
|---|---|
| Purpose | What has actually been tested |
| Status | Proposed |
| Last updated | 2026-11-06 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Test plan](../09-testing/test-plan.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Category | Count |
|---|---|
| Tests that exist | 65 |
| Tests inspected | 65 |
| Tests executed | 62 |
| Tests passed | 62 |
| Tests failed | 0 |
| Tests missing | All other planned tests (see test plan) |

Reason: 65 tests: 52 unit tests (17 for the model client, 17 for the backup, 8 for tracing, 7 for starting the MLflow server, 3 for the result export), 10 integration tests with the Mac model server (2 of them also with the MLflow server) and 3 with the transformers backend. On 6 November 2026 the 52 unit tests and the 10 Mac tests passed. The 3 transformers tests need the demo packages and last ran on 1 November 2026. Steps 0.1 to 0.6 and 1.2 were also checked with the verification loop (rules C12, C13), see docs/HANDOVER.md. CI comes in step 1.4. Update this file at the end of every step.

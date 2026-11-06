# Testing status

| Field | Value |
|---|---|
| Purpose | What has actually been tested |
| Status | Proposed |
| Last updated | 2026-11-07 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Test plan](../09-testing/test-plan.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Category | Count |
|---|---|
| Tests that exist | 92 |
| Tests inspected | 92 |
| Tests executed | 89 |
| Tests passed | 89 |
| Tests failed | 0 |
| Tests missing | All other planned tests (see test plan) |

Reason: 92 tests: 73 unit tests (21 for the model client, 18 for the backup, 11 for tracing, 7 for starting the MLflow server, 4 for the result export, 5 for prompts, 7 for the result check), 16 Mac tests (8 with the model server, 2 also with the MLflow server, 6 for the model files) and 3 with the transformers backend. On 7 November 2026 the 73 unit tests and the 16 Mac tests passed. The 3 transformers tests need the demo packages and last ran on 1 November 2026. Mac tests run only with uv run pytest -m mac. Steps 0.1 to 0.6, 1.2 and 1.3 were also checked with the verification loop (rules C12, C13), see docs/HANDOVER.md. CI comes in step 1.4. Update this file at the end of every step.

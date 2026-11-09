# Testing status

| Field | Value |
|---|---|
| Purpose | What has actually been tested |
| Status | Proposed |
| Last updated | 2026-11-09 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Test plan](../09-testing/test-plan.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Category | Count |
|---|---|
| Tests that exist | 112 |
| Tests inspected | 112 |
| Tests executed | 109 |
| Tests passed | 109 |
| Tests failed | 0 |
| Tests missing | All other planned tests (see test plan) |

Reason: 112 tests: 91 unit tests (22 for the model client, 18 for the backup, 17 for the evaluation gate, 11 for tracing, 7 for starting the MLflow server, 7 for the result check, 5 for prompts, 4 for the result export), 2 CI model tests with llama.cpp and Qwen3.5-0.8B, 16 Mac tests (8 with the model server, 2 also with the MLflow server, 6 for the model files) and 3 with the transformers backend. On 9 November 2026 the 91 unit tests and the 2 CI model tests passed in CI (run 42652265120) and the 16 Mac tests passed on the Mac. The 3 transformers tests need the demo packages and last ran on 1 November 2026. Mac tests run only with uv run pytest -m mac. CI model tests run only with uv run pytest -m ci_model. A deliberately failing test on a test branch turned CI red (step 1.4). Steps 0.1 to 0.6 and 1.2 to 1.4 were also checked with the verification loop (rules C12, C13), see docs/HANDOVER.md. Update this file at the end of every step.

# Testing status

| Field | Value |
|---|---|
| Purpose | What has actually been tested |
| Status | Proposed |
| Last updated | 2026-11-13 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Test plan](../09-testing/test-plan.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Category | Count |
|---|---|
| Tests that exist | 154 |
| Tests inspected | 154 |
| Tests executed | 151 |
| Tests passed | 151 |
| Tests failed | 0 |
| Tests missing | All other planned tests (see test plan) |

Reason: 154 tests: 133 unit tests (23 for the model client, 18 for the backup, 18 for the GPU smoke test, 17 for the evaluation gate, 12 for tracing, 11 for the result check, 7 for the GPU candidates, 7 for the GPU notebooks, 7 for starting the MLflow server, 5 for prompts, 4 for the result export, 4 for the result import), 2 CI model tests with llama.cpp and Qwen3.5-0.8B, 16 Mac tests (8 with the model server, 2 also with the MLflow server, 6 for the model files) and 3 with the transformers backend. On 13 November 2026 the 133 unit tests and the 2 CI model tests passed in CI (run 43518202012) and the 16 Mac tests passed on the Mac. The 3 transformers tests need the demo packages and last ran on 1 November 2026. Mac tests run only with uv run pytest -m mac. CI model tests run only with uv run pytest -m ci_model. A deliberately failing test on a test branch turned CI red (step 1.4). The GPU smoke test ran on Kaggle and Colab (step 1.5). Steps 0.1 to 0.6 and 1.2 to 1.5 were also checked with the verification loop (rules C12, C13), see docs/HANDOVER.md. Update this file at the end of every step.

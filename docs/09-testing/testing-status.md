# Testing status

| Field | Value |
|---|---|
| Purpose | What has actually been tested |
| Status | Proposed |
| Last updated | 2026-11-20 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Test plan](../09-testing/test-plan.md) |

> Implementation status: see docs/WORK_PLAN.md, section 1 (current state). Test results are in docs/HANDOVER.md.

| Category | Count |
|---|---|
| Tests that exist | 372 |
| Tests inspected | 372 |
| Tests executed | 369 |
| Tests passed | 369 |
| Tests failed | 0 |
| Tests missing | All other planned tests (see test plan) |

Reason: 372 tests: 348 unit tests (44 for login, passwords and sessions, 25 for the chat page, 25 for the page server, its security headers and the login and sign-up pages, 23 for the model client, 18 for the backup, 18 for the GPU smoke test, 17 for the evaluation gate, 17 for the saved chats, 14 for the health check, 14 for the app database, 14 for the admin panel, 12 for tracing, 11 for the result check, 11 for the harness settings and context, 12 for the API, 9 for harness.run(), 9 for the dashboard, 8 for the admin commands, 7 for the GPU candidates, 7 for the GPU notebooks, 7 for starting the MLflow server, 6 for the demo, 5 for prompts, 4 for the result export, 4 for the result import, 4 for the files of the demo Space, 3 for the imports between the layers), 2 CI model tests with llama.cpp and Qwen3.5-0.8B, 19 Mac tests (8 with the model server, 2 also with the MLflow server, 6 for the model files, 3 for the API and the harness) and 3 with the transformers backend. On 20 November 2026 the 348 unit tests and the 2 CI model tests passed in CI, also on main (run 44653215637). The 19 Mac tests passed on the Mac on 17 November 2026. On 20 November 2026, with pydantic 2.12.5, 16 of them passed in a copy of the repo and the 3 that need the MLflow server were skipped because it was not running. The 3 transformers tests need the demo packages, download Qwen3.5-0.8B and last ran on 1 November 2026, with torch 2.15.0. Mac tests run only with uv run pytest -m mac. CI model tests run only with uv run pytest -m ci_model. The transformers tests run only with uv run --group demo pytest -m transformers. A deliberately failing test on a test branch turned CI red (step 1.4). The GPU smoke test ran on Kaggle and Colab (step 1.5). A real answer streamed through the API on the Mac (step 1.6). The dashboard went live on GitHub Pages (step 1.7). The demo chat page ran on the Mac with make demo and answered on its ZeroGPU Space (step 1.8). The health check opened an issue for a wrong address (step 1.9). A streamed answer from the main model appeared in the chat page in the browser and a member could not open another user's chat or the admin panel (step 1.10). Steps 0.1 to 0.6 and 1.2 to 1.10 were also checked with the verification loop (rules C12, C13), see docs/HANDOVER.md. Update this file at the end of every step.

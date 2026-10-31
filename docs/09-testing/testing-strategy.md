# Testing strategy

| Field | Value |
|---|---|
| Purpose | How the platform will be tested |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Test plan](../09-testing/test-plan.md), [CI/CD pipeline](../10-deployment-and-operations/ci-cd-pipeline.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Level | What | Tool | Where it runs | Phase |
|---|---|---|---|---|
| Unit | Single functions | pytest | CI | 1.4 onward |
| Integration | Model calls with a tiny model (Qwen3.5-0.8B on CPU) | pytest | CI | 1.4 |
| API | Endpoint contracts | pytest | CI | 1.6, 13.1 |
| Quality evaluation | Route metrics on frozen test sets | eval_run.py | Mac, Colab, Kaggle | 2 onward |
| Evaluation gate | Fails CI if committed scores drop | CI | CI | 1.4 |
| Security | Injection, sandbox escape, access leak, web leak | pytest | Mac and CI | 8.4, 11.2, 12 |
| Performance | RAM, latency, load | scripts | Mac, Kaggle | 0.4, 5.5, 15.4 |
| End-to-end | Upload to cited answer | pytest | CI | 13.5 |
| Human check | 20 judged answers | sheet | Owner | 2.5 |
| Verification loop | Local output and verification numbers match the coding assistant's expected output | Check command in WORK_PLAN.md section 5.2 | Mac | Every step from 0.1 (rules C12, C13) |

Static checks on every push: ruff, mypy, pip-audit, secret scan (1.4).

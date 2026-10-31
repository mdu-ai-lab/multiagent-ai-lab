# Deployment guide

| Field | Value |
|---|---|
| Purpose | How each environment will be set up |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [CI/CD pipeline](../10-deployment-and-operations/ci-cd-pipeline.md), [Deployment architecture](../04-architecture/deployment-architecture.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

Commands are written when each step starts (rule C5). This guide lists what will exist.

| Environment | How it is set up | Step |
|---|---|---|
| Mac | uv project, Docker Qdrant and MLflow, native llama-swap | 0.1 to 0.3, 1.2 |
| Colab and Kaggle | Notebook template: clone at a commit, install with uv, start vLLM | 1.5 |
| Dashboard | pages.yml after CI passes on main | 1.7 |
| Demo | demo.yml uploads demo/ and src/ to the Space | 1.8 |
| Company server | Container images from GHCR plus a GPU compose file | 15.1, 15.2 |
| One-command setup | make setup, make up, make down, make eval | 16.1 |

## Deployment checklist (per release)

1. CI green on main.
2. Plan and changelog updated.
3. Version tag created.
4. Dashboard and demo show the new version.
5. Health check passes.

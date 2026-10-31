# Secrets management

| Field | Value |
|---|---|
| Purpose | Where tokens live and where they must not |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Environment configuration](../10-deployment-and-operations/environment-configuration.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Secret | Used by | Stored in | Never in |
|---|---|---|---|
| GitHub token for Colab and Kaggle pushes | Notebooks | Colab Secrets, Kaggle Secrets | Git, Drive, notebooks |
| Hugging Face token for demo deploys | demo.yml | GitHub Secrets | Git, logs |
| rclone Google Drive token | make backup | rclone config on the Mac | Git, Drive |
| User passwords (Phase 13) | auth.py | Hashed in the database | Logs, traces |

.env holds local settings and is ignored by Git. .env.example lists names without values (0.1). The secret scan in CI checks every push (1.4).

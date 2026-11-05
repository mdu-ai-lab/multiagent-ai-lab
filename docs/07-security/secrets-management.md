# Secrets management

| Field | Value |
|---|---|
| Purpose | Where tokens live and where they must not |
| Status | Proposed |
| Last updated | 2026-11-05 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Environment configuration](../10-deployment-and-operations/environment-configuration.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Secret | Used by | Stored in | Never in |
|---|---|---|---|
| GitHub token for Colab and Kaggle pushes | Notebooks | Colab Secrets, Kaggle Secrets | Git, Drive, notebooks |
| Hugging Face token for demo deploys | demo.yml | GitHub Secrets | Git, logs |
| rclone Google Drive token | make backup | rclone config on the Mac | Git, Drive |
| User passwords (from 1.10) | auth.py | Hashed in the database | Logs, traces |

.env holds local settings and is ignored by Git. .env.example lists names without values (0.1). The secret scan in CI checks every push (1.4).

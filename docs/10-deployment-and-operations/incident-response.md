# Incident response

| Field | Value |
|---|---|
| Purpose | What to do when something breaks |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Monitoring and logging](../10-deployment-and-operations/monitoring-and-logging.md), [Risk register](../12-project-management/risk-register.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

PROPOSED runbook for a prototype run by one owner.

| Incident | First action | Then |
|---|---|---|
| Dashboard or demo down (health issue opened) | Check the last Actions run | Fix, push, close the issue |
| Free tier changed or blocked | Stop deploys to that service | Re-check limits, record a decision, update the plan |
| Secret exposed | Revoke the token at once | Create a new one in Secrets, check history |
| Private file pushed or uploaded by mistake | Remove it from the Space or repo and revoke links | Remove it from Git history, record what happened |
| SSD lost or damaged | Clone from GitHub | Restore Drive backup, re-create models and indexes |
| CI broken after dependency update | Revert the update | Fix, then update again through CI |

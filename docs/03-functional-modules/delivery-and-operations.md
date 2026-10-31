# Module: Delivery and operations

| Field | Value |
|---|---|
| Purpose | Specification of the delivery and operations module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | CI, live site, demo, backup and monitoring |
| Actors | Owner, group, visitors |
| Functional requirements | FR-OPS-001 to FR-OPS-005 |
| Business rules | BR-COST-001 |
| Planned files | export_results.py, site_build.py, workflows |
| Models and tools | GitHub Actions, Pages, ZeroGPU, rclone, MLflow |
| Data entities | — |
| API endpoints | — |
| Input validation | Pushes to main |
| Expected outputs | Live dashboard, demo, backups, issues |
| Error conditions | Health check opens an issue |
| Events and notifications | Weekly health check |
| Security considerations | Tokens in CI, public demo content |
| Testing requirements | CI fail test, restore test, health test |
| Acceptance criteria | AT-0.6, AT-1.1 to AT-1.9 |
| Plan and paper references | Phases 0 and 1 |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

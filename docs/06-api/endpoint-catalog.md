# Endpoint catalog

| Field | Value |
|---|---|
| Purpose | Planned endpoints by phase |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [API standards](../06-api/api-standards.md), [Modules](../03-functional-modules/README.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

No route exists yet. Only the 4 endpoints in step 1.6 are named in the plan. Paths are proposals.

| Method | Path (proposed) | Purpose | Auth | Phase | Status |
|---|---|---|---|---|---|
| GET | /v1/health | Service is up | None | 1.6 | Not implemented |
| GET | /v1/version | Code and pipeline version | None | 1.6 | Not implemented |
| GET | /v1/models | Models in the active profile | Until 13: none. After: login | 1.6 | Not implemented |
| POST | /v1/chat | Chat and file questions, streamed | Until 13: none. After: login | 1.6, 6, 7, 8 | Not implemented |

## Capabilities planned without fixed paths

| Capability | Phase | Path |
|---|---|---|
| Upload a file | 3.1 | REQUIRES CONFIRMATION |
| Job status | 3.1 | REQUIRES CONFIRMATION |
| Summaries | 9 | REQUIRES CONFIRMATION |
| Graph questions | 9A.4 | Through POST /v1/chat (router picks the graph route) |
| Build or rebuild a collection's graph | 9A.2 | REQUIRES CONFIRMATION |
| Notebooks, notes and study outputs | 9B | REQUIRES CONFIRMATION |
| Extraction and export | 10 | REQUIRES CONFIRMATION |
| Login | 13.1 | REQUIRES CONFIRMATION |
| Feedback | 13.4 | REQUIRES CONFIRMATION |

Rule A: each feature phase adds its endpoint when the feature is built. This catalog is updated then.

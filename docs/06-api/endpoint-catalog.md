# Endpoint catalog

| Field | Value |
|---|---|
| Purpose | Planned endpoints by phase |
| Status | Proposed |
| Last updated | 2026-11-13 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [API standards](../06-api/api-standards.md), [Modules](../03-functional-modules/README.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

The 4 endpoints of step 1.6 exist in src/mrag/api.py (WORK_PLAN.md D45). They are experimental until Phase 13 freezes the API.

| Method | Path | Purpose | Auth | Phase | Status |
|---|---|---|---|---|---|
| GET | /v1/health | Service is up | None | 1.6 | Implemented (experimental) |
| GET | /v1/version | Code and pipeline version | None | 1.6 | Implemented (experimental) |
| GET | /v1/models | Models in the active profile, read from configs/models.yaml without a model call | Until 1.10: none. After: login | 1.6 | Implemented (experimental) |
| POST | /v1/chat | Chat and file questions, streamed | Until 1.10: none. After: login | 1.6, 6, 7, 8 | Implemented (experimental) |

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
| Login, sign-up, account and admin | 1.10 | Paths set in 1.10 |
| Feedback | 13.4 | REQUIRES CONFIRMATION |

Rule A: each feature phase adds its endpoint when the feature is built. This catalog is updated then.

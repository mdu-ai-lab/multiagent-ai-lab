# API standards

| Field | Value |
|---|---|
| Purpose | Proposed conventions for the /v1 API |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Endpoint catalog](../06-api/endpoint-catalog.md), [Error handling](../06-api/error-handling.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Topic | Proposed standard | Source |
|---|---|---|
| Framework | FastAPI | 1.6 |
| Versioning | All routes under /v1. Marked experimental until Phase 13 freezes it | 1.6, 13.1 |
| Documentation | Generated automatically by FastAPI | 1.6 |
| Streaming | Chat answers stream word by word | 6.1 |
| Validation | Pydantic models for every request and response | Design choice |
| Authentication | Login with tokens from Phase 13 | 13.1 |
| Rate limiting | Requests per minute per user from Phase 13 | 12.4, 13.1 |
| Pagination, filtering, sorting | Needed for lists (documents, jobs). Style REQUIRES CONFIRMATION | — |
| Idempotency | Upload is idempotent by sha256 (3.5). Other endpoints: REQUIRES CONFIRMATION | 3.5 |
| Deprecation | New behaviour after the freeze goes to a new version | Design choice |

pagination-filtering-sorting.md is not a separate document because no list endpoints exist yet.

# Module: Extraction

| Field | Value |
|---|---|
| Purpose | Specification of the extraction module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Reliable JSON from documents |
| Actors | Member, MCP client |
| Functional requirements | FR-EXT-001 to FR-EXT-004 |
| Business rules | BR-EXT-001 |
| Planned files | extract.py |
| Models and tools | Model server JSON schema mode, Pydantic |
| Data entities | Schema files in configs/schemas |
| API endpoints | Extract and export endpoints (paths REQUIRES CONFIRMATION) |
| Input validation | Document plus schema |
| Expected outputs | Validated JSON, CSV or Excel |
| Error conditions | After 2 failed retries the user reviews |
| Events and notifications | — |
| Security considerations | Values not present in the source |
| Testing requirements | JSON validity and field accuracy with Wilson CI |
| Acceptance criteria | AT-10.1 to AT-10.4 |
| Plan and paper references | Phase 10 [Journal, Sec 3.3, p. 7; Sec 5.2, p. 21]; [Billah, Abstract, p. i] |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

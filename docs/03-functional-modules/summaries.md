# Module: Summaries

| Field | Value |
|---|---|
| Purpose | Specification of the summaries module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Summaries that miss nothing |
| Actors | Member |
| Functional requirements | FR-SUM-001, FR-SUM-002 |
| Business rules | BR-GND-002 |
| Planned files | summary.py |
| Models and tools | Main model, pandas |
| Data entities | Section summaries (storage REQUIRES CONFIRMATION) |
| API endpoints | Summary endpoint (path REQUIRES CONFIRMATION) |
| Input validation | Document or review set, length option |
| Expected outputs | Summary with citations and statistics block |
| Error conditions | — |
| Events and notifications | — |
| Security considerations | Invented numbers |
| Testing requirements | Coverage and FSCR against top-k RAG |
| Acceptance criteria | AT-9.1 to AT-9.3 |
| Plan and paper references | Phase 9 [Wahab, Sec 8.3, p. 44] |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

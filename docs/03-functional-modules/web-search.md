# Module: Web search

| Field | Value |
|---|---|
| Purpose | Specification of the web search module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Bring in online information on request |
| Actors | Member |
| Functional requirements | FR-WEB-001 to FR-WEB-003 |
| Business rules | BR-PRIV-002, BR-WEB-001 |
| Planned files | web.py |
| Models and tools | smolagents WebSearchTool, Docling HTML |
| Data entities | — |
| API endpoints | Chat endpoint with web toggle |
| Input validation | Rewritten question |
| Expected outputs | Answer with [W#] URL citations |
| Error conditions | Rate limits get a retry and a message |
| Events and notifications | — |
| Security considerations | Leaking file text, malicious pages |
| Testing requirements | Leak test, toggle test |
| Acceptance criteria | AT-8.1 to AT-8.4 |
| Plan and paper references | Phase 8 |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

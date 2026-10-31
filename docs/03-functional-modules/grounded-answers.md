# Module: Grounded answers

| Field | Value |
|---|---|
| Purpose | Specification of the grounded answers module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Produce cited answers or refuse |
| Actors | Member |
| Functional requirements | FR-QA-001 to FR-QA-005, FR-CHAT-002 |
| Business rules | BR-GND-001 |
| Planned files | qa.py, grounding.py |
| Models and tools | Main model |
| Data entities | — |
| API endpoints | Chat endpoint |
| Input validation | Question, ranked sources |
| Expected outputs | Streamed answer with [S#] citations and highlight data |
| Error conditions | Missing evidence leads to refusal. Unsupported sentences removed or marked |
| Events and notifications | — |
| Security considerations | Prompt injection through sources |
| Testing requirements | Citation validity, claim check, refusal F1 |
| Acceptance criteria | AT-6.1 to AT-6.5 |
| Plan and paper references | Phase 6 [Wahab, Sec 8.3, p. 44; Ch. 7, p. 35] |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

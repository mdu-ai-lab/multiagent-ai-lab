# Module: Agents and memory

| Field | Value |
|---|---|
| Purpose | Specification of the agents and memory module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Send each request to the right route and remember the chat |
| Actors | Member, MCP client |
| Functional requirements | FR-AGT-001 to FR-AGT-003, FR-QA-006, FR-CHAT-001, FR-CHAT-003 |
| Business rules | BR-AGT-001 |
| Planned files | router.py, graph.py, planner.py, memory.py |
| Models and tools | LangGraph, Qwen3.5-2B helper |
| Data entities | Chat thread (LangGraph checkpoints) |
| API endpoints | Chat endpoint |
| Input validation | Message, chosen files, state |
| Expected outputs | Route decision, answer |
| Error conditions | Low confidence leads to the main model or a question. Limits stop loops |
| Events and notifications | — |
| Security considerations | Router manipulation by user text |
| Testing requirements | Routing accuracy, loop limits, fallbacks |
| Acceptance criteria | AT-7.1 to AT-7.5 |
| Plan and paper references | Phase 7 [Chakravorty, Abstract, p. iii; Sec 8.7, p. 47] |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

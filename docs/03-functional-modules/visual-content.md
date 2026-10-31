# Module: Visual content

| Field | Value |
|---|---|
| Purpose | Specification of the visual content module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Make charts, figures and tables searchable |
| Actors | Worker |
| Functional requirements | FR-VIS-001 |
| Business rules | — |
| Planned files | figures.py |
| Models and tools | Qwen3.5-9B vision (Mac), GPU profile model |
| Data entities | Element (model-generated description) |
| API endpoints | None of its own |
| Input validation | Image crops from parsed pages |
| Expected outputs | Text description linked to page and box |
| Error conditions | Vision model failure falls back to text only (7.4) |
| Events and notifications | — |
| Security considerations | Descriptions could contain hidden instructions copied from images |
| Testing requirements | Parser comparison and with/without test |
| Acceptance criteria | AT-4.1 to AT-4.3 |
| Plan and paper references | Phase 4 [Chakravorty, Sec 8.6, p. 45] |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

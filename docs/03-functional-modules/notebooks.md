# Module: Notebooks and study tools

| Field | Value |
|---|---|
| Purpose | Specification of the notebooks and study tools module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Topic workspaces with study outputs |
| Actors | Member |
| Functional requirements | FR-NB-001 to FR-NB-003 |
| Business rules | BR-NB-001, BR-ACC-001 |
| Planned files | notebook.py, study.py |
| Models and tools | Main model, summary route, knowledge graph |
| Data entities | Notebook, note (storage REQUIRES CONFIRMATION) |
| API endpoints | Notebook and study endpoints (paths REQUIRES CONFIRMATION) |
| Input validation | Chosen sources must be in accessible collections |
| Expected outputs | Notes, briefing, study guide, FAQ, timeline, flashcards, quiz, mind map, all with citations |
| Error conditions | Unsupported items removed or marked by claim check |
| Events and notifications | — |
| Security considerations | Made-up facts in learning material |
| Testing requirements | Citation and claim check, hand-check of 20 flashcards and quiz questions |
| Acceptance criteria | AT-9B.1 to AT-9B.4 |
| Plan and paper references | Phase 9B (D19) |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

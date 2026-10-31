# Module: Calculations

| Field | Value |
|---|---|
| Purpose | Specification of the calculations module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Exact numbers and plots from tables |
| Actors | Member |
| Functional requirements | FR-CALC-001 to FR-CALC-003 |
| Business rules | BR-SEC-001 |
| Planned files | calc.py |
| Models and tools | smolagents CodeAgent, Docker, pandas, matplotlib |
| Data entities | — |
| API endpoints | Chat endpoint |
| Input validation | Question plus found tables |
| Expected outputs | Number or PNG plot with code and source |
| Error conditions | Failure shows the table instead (7.4) |
| Events and notifications | — |
| Security considerations | Sandbox escape |
| Testing requirements | Escape tests, TAT-DQA math |
| Acceptance criteria | AT-11.1 to AT-11.4 |
| Plan and paper references | Phase 11 |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

# Module: Audio

| Field | Value |
|---|---|
| Purpose | Specification of the audio module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Questions over recordings |
| Actors | Member |
| Functional requirements | FR-AUD-001 |
| Business rules | — |
| Planned files | audio.py |
| Models and tools | whisper.cpp or Granite Speech 5.0 (chosen by test) |
| Data entities | Element with time range |
| API endpoints | Upload endpoint |
| Input validation | Audio file |
| Expected outputs | Timestamped transcript chunks |
| Error conditions | — |
| Events and notifications | — |
| Security considerations | Large files, personal data in speech |
| Testing requirements | Word error rate, time-range citation |
| Acceptance criteria | AT-14.1, AT-14.2 |
| Plan and paper references | Phase 14 |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

# Module: Ingestion

| Field | Value |
|---|---|
| Purpose | Specification of the ingestion module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Turn uploaded files into structured elements and page images |
| Actors | Member, worker |
| Functional requirements | FR-ING-001 to FR-ING-006 |
| Business rules | BR-VER-001 |
| Planned files | jobs.py, worker.py, parse.py, versioning.py |
| Models and tools | Docling, OCR engine (chosen in 3.3) |
| Data entities | User, collection, document, document version, element, job |
| API endpoints | Upload and job endpoints (paths REQUIRES CONFIRMATION) |
| Input validation | File type checked by content. 50 MB and 1,000 pages max (NFR-SEC-004) |
| Expected outputs | Elements with page, heading path and box. Page images |
| Error conditions | Unsupported type, parse failure, OCR failure, crash mid-job |
| Events and notifications | Job status changes |
| Security considerations | Malicious files, hidden instructions in text |
| Testing requirements | Parse each type, kill-and-resume, duplicate and version tests |
| Acceptance criteria | AT-3.1 to AT-3.5 |
| Plan and paper references | Phase 3 [Chakravorty, Sec 7.3.1, p. 22]; [Journal, Sec 4.1, p. 9] |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

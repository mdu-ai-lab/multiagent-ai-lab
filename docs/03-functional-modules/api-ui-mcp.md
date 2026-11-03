# Module: API, UI and MCP

| Field | Value |
|---|---|
| Purpose | Specification of the api, ui and mcp module |
| Status | Proposed |
| Last updated | 2026-11-04 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Item | Detail |
|---|---|
| Purpose | One contract for every client |
| Actors | Member, Platform admin, MCP client |
| Functional requirements | FR-API-001, FR-API-002, FR-UI-001, FR-UI-002, FR-ADM-002, FR-MCP-001, FR-FBK-001 |
| Business rules | BR-ACC-001 |
| Planned files | service.py, api.py, auth.py, ui.py, admin.py, translations.py, templates/, static/ |
| Models and tools | FastAPI, Jinja2, Gradio 6 (demo) |
| Data entities | User, session, chat, message |
| API endpoints | See endpoint catalog |
| Input validation | HTTP requests |
| Expected outputs | JSON and streamed responses |
| Error conditions | See error handling |
| Events and notifications | — |
| Security considerations | No login before 1.10 (SF-01) |
| Testing requirements | API tests, end-to-end test |
| Acceptance criteria | AT-1.6, AT-1.10, AT-13.1 to AT-13.5 |
| Plan and paper references | Phases 1 and 13 |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

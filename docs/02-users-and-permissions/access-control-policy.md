# Access control policy

| Field | Value |
|---|---|
| Purpose | Proposed rules for who can reach which data |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Role permission matrix](../02-users-and-permissions/role-permission-matrix.md), [Authentication and authorization](../07-security/authentication-and-authorization.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| ID | Policy | Enforcement point (planned) | Status |
|---|---|---|---|
| ACP-001 | Every request belongs to a logged-in user, except the public demo | auth.py (13.1) | Not implemented |
| ACP-002 | Search always carries the user's allowed collections as a filter | retrieve.py (5.3) | Not implemented |
| ACP-003 | The filter is added in code, never chosen by a model | retrieve.py (5.3) | Not implemented |
| ACP-004 | MCP tools act with the rights of the token's user | Gradio MCP mode (13.3) | Not implemented |
| ACP-005 | The demo holds only public sample documents | demo/ (1.8) | Not implemented |
| ACP-006 | Before Phase 13 the API has no login, so it must only listen on the Mac itself | api.py (1.6) | Recommendation. Not in WORK_PLAN.md yet |
| ACP-007 | The graph route applies the same collection filter as retrieve.py | graphrag.py (9A.4) | Not implemented |
| ACP-008 | Notebooks use the existing collection access rules | notebook.py (9B.1) | Not implemented |

ACP-006 is a recommendation from this documentation review, not an existing plan decision. See finding SF-01 in the [threat model](../07-security/threat-model.md).

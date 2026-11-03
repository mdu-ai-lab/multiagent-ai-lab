# API authentication

| Field | Value |
|---|---|
| Purpose | How API callers will prove who they are |
| Status | Proposed |
| Last updated | 2026-11-04 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Authentication and authorization](../07-security/authentication-and-authorization.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

The single policy document is [authentication and authorization](../07-security/authentication-and-authorization.md). Summary: login with hashed passwords and sessions from step 1.10. Tokens for other apps from 13.1. MCP uses a login token (13.3).

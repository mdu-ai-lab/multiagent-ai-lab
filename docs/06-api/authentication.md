# API authentication

| Field | Value |
|---|---|
| Purpose | How API callers will prove who they are |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Authentication and authorization](../07-security/authentication-and-authorization.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

The single policy document is [authentication and authorization](../07-security/authentication-and-authorization.md). Summary: no login until Phase 13. Then tokens and hashed passwords (13.1). MCP uses a login token (13.3).

# User types

| Field | Value |
|---|---|
| Purpose | Planned actors and roles |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Role permission matrix](../02-users-and-permissions/role-permission-matrix.md), [Stakeholders](../00-project-overview/stakeholders.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

Role names below are proposals. The plan states that users and collections live in the database and each user sees only their collections (step 12.4). Exact roles beyond that: REQUIRES CONFIRMATION.

| Role | Purpose | Scope | Status |
|---|---|---|---|
| Member | Uses chat, upload, search, summaries, extraction and calculations | Own collections and collections shared with them | Proposed |
| Platform admin | Creates users and collections and manages access | Whole local installation | Proposed. REQUIRES CONFIRMATION |
| Demo visitor | Uses the public demo | Public sample documents only. No login | Planned (1.8) |
| MCP client | Another AI tool calling search, ask and extract | Same rights as the token's user | Planned (13.3) |
| Repo maintainer | Develops through GitHub | GitHub organization role Owner or Admin (Q8) | Planned (0.1). Role choice open |

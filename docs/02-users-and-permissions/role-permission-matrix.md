# Role permission matrix

| Field | Value |
|---|---|
| Purpose | What each proposed role may do |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [User types](../02-users-and-permissions/user-types.md), [Access control policy](../02-users-and-permissions/access-control-policy.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

Legend: Y = allowed, O = own or shared collections only, N = not allowed, ? = REQUIRES CONFIRMATION. Enforcement is planned in Phase 12 and Phase 13. Nothing is enforced yet.

| Operation | Member | Platform admin | Demo visitor | MCP client |
|---|---|---|---|---|
| Chat without files | Y | Y | Y | N |
| Upload files | O | Y | N | N |
| Ask questions over files | O | Y | Public samples | O |
| Web search (opt-in) | Y | Y | ? | N |
| Summaries | O | Y | Public samples | N |
| Extraction | O | Y | Public samples | O |
| Calculations and plots | O | Y | Public samples | N |
| Graph questions (GraphRAG) | O | Y | Public samples | ? |
| Notebooks and study outputs | O | Y | Public samples | N |
| Build or rebuild a collection's graph | ? | Y | N | N |
| Delete files | O | Y | N | N |
| Create users and collections | N | Y | N | N |
| Give feedback | Y | Y | ? | N |
| View monitoring | N | Y | N | N |

Demo visitor rights depend on what the demo exposes, which grows each phase (rule A).

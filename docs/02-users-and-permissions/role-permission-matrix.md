# Role permission matrix

| Field | Value |
|---|---|
| Purpose | What each proposed role may do |
| Status | Proposed |
| Last updated | 2026-11-15 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [User types](../02-users-and-permissions/user-types.md), [Access control policy](../02-users-and-permissions/access-control-policy.md) |

> Implementation status: see docs/WORK_PLAN.md, section 1 (current state). Test results are in docs/HANDOVER.md.

Legend: Y = allowed, O = own or shared collections only, N = not allowed, ? = REQUIRES CONFIRMATION. Enforcement is planned from step 1.10 (login and roles) and in Phase 12 and Phase 13. Nothing is enforced yet. Limited = only while an admin allows guest mode, up to the guest message limit (D49).

| Operation | Member | Platform admin | Guest | Demo visitor | MCP client |
|---|---|---|---|---|---|
| Chat without files | Y | Y | Limited | Y | N |
| Upload files | O | Y | N | N | N |
| Ask questions over files | O | Y | N | Public samples | O |
| Web search (opt-in) | Y | Y | N | ? | N |
| Summaries | O | Y | N | Public samples | N |
| Extraction | O | Y | N | Public samples | O |
| Calculations and plots | O | Y | N | Public samples | N |
| Graph questions (GraphRAG) | O | Y | N | Public samples | ? |
| Notebooks and study outputs | O | Y | N | Public samples | N |
| Build or rebuild a collection's graph | ? | Y | N | N | N |
| Delete files | O | Y | N | N | N |
| Create users and collections | N | Y | N | N | N |
| Give feedback | Y | Y | N | ? | N |
| View monitoring | N | Y | N | N | N |
| Read another user's chats | N | N | N | N | N |

Demo visitor rights depend on what the demo exposes, which grows each phase (rule A).

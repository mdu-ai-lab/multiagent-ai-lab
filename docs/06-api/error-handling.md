# Error handling

| Field | Value |
|---|---|
| Purpose | Proposed error behaviour |
| Status | Proposed |
| Last updated | 2026-11-05 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [API standards](../06-api/api-standards.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Situation | Proposed behaviour | Source |
|---|---|---|
| Invalid input | Clear message, request rejected | 13.1 |
| Unsupported file type | Clear message | 3.2 |
| Over limits (size, pages, rate) | Clear message | 12.4 |
| Evidence missing | Normal answer that says "I could not find this in your files" (not an error) | 6.4 |
| Model or tool failure | Fallback path, logged in the trace | 7.4 |
| Timeout | Stop at 120 s and fall back | 7.4 |

Error response format (fields, codes): REQUIRES CONFIRMATION in step 13.1.

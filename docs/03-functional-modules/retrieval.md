# Module: Retrieval

| Field | Value |
|---|---|
| Purpose | Specification of the retrieval module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Find the right evidence fast |
| Actors | Q&A, summary, compare agents |
| Functional requirements | FR-RET-001 to FR-RET-004 |
| Business rules | BR-ACC-001, BR-VER-001 |
| Planned files | chunking.py, embed.py, index.py, retrieve.py, rerank.py |
| Models and tools | Qdrant, Qwen3-VL-Embedding-2B, Qwen3-VL-Reranker-2B |
| Data entities | Chunk (Qdrant point) |
| API endpoints | Internal only |
| Input validation | Query plus filters |
| Expected outputs | Top 6 to 8 ranked chunks |
| Error conditions | Empty result leads to refusal |
| Events and notifications | — |
| Security considerations | Filter bypass would leak data |
| Testing requirements | Ablation ladder, filter test, latency |
| Acceptance criteria | AT-5.1 to AT-5.5 |
| Plan and paper references | Phase 5 [Chakravorty, Sec 7.4.3, p. 24; App. A, p. 57] |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

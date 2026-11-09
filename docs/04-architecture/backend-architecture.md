# Backend architecture

| Field | Value |
|---|---|
| Purpose | Planned backend layers and modules |
| Status | Proposed |
| Last updated | 2026-11-09 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [System architecture](../04-architecture/system-architecture.md), [Agent harness](../04-architecture/agent-harness.md), [Project structure](../11-development-standards/project-structure.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Layer | Planned files | Responsibility |
|---|---|---|
| API | api.py, auth.py, ui.py | HTTP under /v1, pages, login (1.10, hardened in Phase 13), streaming |
| Service | service.py | Core functions shared by API, demo, tests and MCP (ADR-008) |
| Orchestration | harness/ package (D43): __init__.py, handle.py, loop.py, router.py, planner.py, memory.py, context.py, settings.py, limits.py, tools.py, retrieval.py, rerank.py, verify.py, guards.py | One entry harness.run() with streamed events, routes, prompt budget, tool list, loop limits, trace totals, chat memory |
| Routes | qa.py, summary.py, extract.py, calc.py, audio.py, graphrag.py | One task each |
| Engines | web.py, injection.py | Web search and page fetch (called by the harness), the injection classifier (called by the harness and the upload worker) |
| Knowledge | ontology.py, kg.py | LinkML ontology, graph extraction and store at upload, graph lookups for harness/retrieval.py at question time (9A) |
| Notebooks | notebook.py, study.py | Notebooks, notes and study outputs (9B) |
| Grounding | harness/verify.py, harness/guards.py | Citations, claim check, refusal, injection rules |
| Retrieval | chunking.py, embed.py, index.py (upload), harness/retrieval.py, harness/rerank.py (question time) | Hybrid search |
| Ingestion | jobs.py, worker.py, parse.py, figures.py, sections.py, pii.py, versioning.py (figures.py and sections.py call llm_client.py directly) | Files to elements |
| Models | llm_client.py | One wrapper for llama.cpp, vLLM and Transformers (ADR-002, NFR-PORT-001) |
| Data | db.py, config.py | SQLAlchemy (SQLite, Postgres later), settings and profiles |
| Evaluation and delivery | eval_*.py, judge.py, export_results.py, site_build.py, tracing.py | Metrics, dashboard data, traces |

All modules are flat in src/<package>/ (rule C2), except the agent harness package src/mrag/harness/ (D43). Package name: mrag unless changed through the AI agent workflow change-request process.

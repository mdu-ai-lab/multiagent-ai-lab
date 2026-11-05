# Backend architecture

| Field | Value |
|---|---|
| Purpose | Planned backend layers and modules |
| Status | Proposed |
| Last updated | 2026-11-05 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [System architecture](../04-architecture/system-architecture.md), [Project structure](../11-development-standards/project-structure.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Layer | Planned files | Responsibility |
|---|---|---|
| API | api.py, auth.py, ui.py | HTTP under /v1, pages, login (1.10, hardened in Phase 13), streaming |
| Service | service.py | Core functions shared by API, demo, tests and MCP (ADR-008) |
| Orchestration | graph.py, router.py, planner.py, memory.py, harness.py | Routes, prompt budget, tool list, loop limits, trace totals, chat memory |
| Routes | qa.py, web.py, summary.py, extract.py, calc.py, audio.py, graphrag.py | One task each |
| Knowledge | ontology.py, kg.py | LinkML ontology, graph extraction and store (9A) |
| Notebooks | notebook.py, study.py | Notebooks, notes and study outputs (9B) |
| Grounding | grounding.py, security.py | Citations, claim check, refusal, injection rules |
| Retrieval | chunking.py, embed.py, index.py, retrieve.py, rerank.py | Hybrid search |
| Ingestion | jobs.py, worker.py, parse.py, figures.py, pii.py, versioning.py | Files to elements |
| Models | llm_client.py | One wrapper for llama.cpp, vLLM and Transformers (ADR-002, NFR-PORT-001) |
| Data | db.py, config.py | SQLAlchemy (SQLite, Postgres later), settings and profiles |
| Evaluation and delivery | eval_*.py, judge.py, export_results.py, site_build.py, tracing.py | Metrics, dashboard data, traces |

All modules are flat in src/<package>/ (rule C2). Package name: mrag unless changed through the AI agent workflow change-request process.

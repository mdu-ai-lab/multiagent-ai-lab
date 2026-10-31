# Architecture overview

| Field | Value |
|---|---|
| Purpose | One-page view of the planned architecture |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [System architecture](../04-architecture/system-architecture.md), [ADRs](../04-architecture/architecture-decision-records/README.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

The planned system has 4 layers:

| Layer | Parts | Detail |
|---|---|---|
| Clients | Gradio UI, live demo, MCP clients | [Frontend architecture](frontend-architecture.md) |
| Service | FastAPI (api.py) over service.py | [Backend architecture](backend-architecture.md) |
| Intelligence | LangGraph supervisor and routes, grounding, retrieval, model client | [System architecture](system-architecture.md) |
| Data and models | Qdrant, SQLite (Postgres later), MLflow, llama.cpp / vLLM / Transformers | [Deployment architecture](deployment-architecture.md) |

The plan's own architecture diagram, copied word for word from WORK_PLAN.md section 8.1:

```
Browser (Gradio UI)  ·  Live demo (ZeroGPU Space)  ·  MCP clients
            │ HTTP /v1 (local)            │ in-process
            ▼                             ▼
        FastAPI (api.py) ───────► service.py (core functions)
                                          │
                     LangGraph supervisor (graph.py)
   Router → chat · document Q&A · compare · web · summary · extract · calc
                     │ Planner–Navigator–Reviewer (max 3, gated)
                     │ grounding.py (citations, claim check, refusal)
          ┌──────────┼───────────────┬──────────────────┐
     retrieve.py  rerank.py      llm_client.py       tools (web.py, calc.py sandbox)
          │                         │
       Qdrant              llama.cpp + llama-swap (Mac) · vLLM (Colab/Kaggle/company) · Transformers (demo)
          ▲
   worker.py: parse.py (Docling) → figures.py → chunking.py → pii.py → embed.py → index.py
   SQLite (users, collections, documents, versions, jobs, chat memory)
   MLflow (experiments, prompts, versions, traces, feedback) → export → results/ → dashboard
```

Key choices: knowledge graph and GraphRAG chosen by test (ADR-017), LinkML ontology (ADR-018), notebooks without audio overviews (ADR-019), verification loop and verification number (ADR-020), coding assistant with a local rules file and HANDOVER.md (ADR-021), names multiagent-ai-lab and mdu-ai-lab (ADR-022), local runtime with llama.cpp (ADR-002), LangGraph plus smolagents (ADR-003), Qdrant (ADR-004), SQLite to Postgres (ADR-005), MLflow (ADR-006), API-first (ADR-008), GitHub Pages plus ZeroGPU (ADR-009).

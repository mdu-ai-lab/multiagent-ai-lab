# System architecture

| Field | Value |
|---|---|
| Purpose | Components, data flow and boundaries of the planned system |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Backend architecture](../04-architecture/backend-architecture.md), [Integration architecture](../04-architecture/integration-architecture.md), [Threat model](../07-security/threat-model.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

All diagrams show the PROPOSED design from WORK_PLAN.md section 8.1. No component exists yet.

## Component diagram (PROPOSED)

```mermaid
flowchart TB
  subgraph Clients
    UI[Gradio UI]
    MCP[MCP clients]
    DEMO[Demo Space]
  end
  API[FastAPI api.py] --> SVC[service.py]
  UI --> API
  MCP --> API
  DEMO -->|in-process| SVC
  SVC --> G[LangGraph supervisor graph.py]
  G --> R[router.py]
  R --> CHAT[chat]
  R --> QA[document Q&A qa.py]
  R --> CMP[compare]
  R --> WEB[web.py]
  R --> SUM[summary.py]
  R --> EXT[extract.py]
  R --> CALC[calc.py sandbox]
  R --> GR2[graphrag.py graph route]
  GR2 --> KGS[(Graph store - format chosen in 9A.3)]
  ONT[ontology.py LinkML] --> KG[kg.py graph extraction] --> KGS
  NB[notebook.py + study.py] --> SUM
  NB --> KGS
  QA --> PL[planner.py loop max 3]
  QA --> GR[grounding.py]
  QA --> RET[retrieve.py + rerank.py]
  RET --> QD[(Qdrant)]
  G --> LLM[llm_client.py]
  LLM --> MS[llama.cpp + llama-swap / vLLM / Transformers]
  WK[worker.py] --> PARSE[parse.py Docling] --> FIG[figures.py] --> CH[chunking.py] --> PII[pii.py] --> EMB[embed.py] --> IDX[index.py] --> QD
  SVC --> DB[(SQLite)]
  G --> ML[(MLflow traces)]
```

## Request flow for a cited answer (PROPOSED)

```mermaid
sequenceDiagram
  participant U as User
  participant A as api.py
  participant G as graph.py
  participant R as retrieve.py
  participant M as Model server
  participant C as grounding.py
  U->>A: question + chosen files
  A->>G: run with user and collection filter
  G->>G: router picks document Q&A
  G->>R: hybrid search with filters
  R-->>G: top 6 to 8 chunks
  G->>M: answer with numbered sources
  M-->>G: draft with [S#]
  G->>C: citation check + claim check
  C-->>A: final answer or refusal
  A-->>U: streamed answer + highlights
```

## Ingestion workflow (PROPOSED)

```mermaid
flowchart LR
  UP[Upload] --> J[Job queued] --> P[Parse + OCR] --> F[Describe figures] --> C[Chunk] --> X[Mask personal data in logs] --> E[Embed] --> I[Index in Qdrant] --> D[Job done]
  P -->|failure| FL[Job failed with reason]
  I -->|optional per collection| KX[Graph extraction with ontology - 9A.2] --> KD[Graph store]
```

## Boundaries

| Boundary | Inside | Outside |
|---|---|---|
| Privacy | Mac: private files, index, MLflow | Colab, Kaggle, GitHub, Drive, demo, dashboard |
| Trust | Code, configs | File text, web pages, user input (treated as data) |
| Failure | Each route has a fallback (7.4) | — |

## Scaling

One user on the Mac first. Multi-user server with Postgres and vLLM in Phase 15. Multi-server scaling is a non-goal for v1.

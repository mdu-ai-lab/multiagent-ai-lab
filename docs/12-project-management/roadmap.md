# Roadmap

| Field | Value |
|---|---|
| Purpose | Phase order |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Milestones](../12-project-management/milestones.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| State | Content |
|---|---|
| Existing functionality | Project setup (step 0.1): settings, database layer, Alembic. Qdrant in Docker (step 0.2). Local model server with 4 models (step 0.3). Mac measurements (step 0.4). Model client (step 0.5) |
| Work in progress | Phase 0. Next: step 0.6 |
| Planned | Phases 0 to 16 (below) |
| Future possibilities | SSO, multi-server scaling, fine-tuning, more languages (not in v1) |

## Why this order (WORK_PLAN.md section 10.1, word for word)

Foundations, delivery and measurement come first so every later feature is tested, versioned and visible from day one. Features then follow the data flow: files are parsed before they can be searched, searched before they can be answered, answered before agents can route them. Security, hardening and the company package come after all routes exist. Handover is last.

## Phase dependencies (section 10.2)

| Phase | Depends on | Reason |
|---|---|---|
| 0 Foundations | — | Base for everything |
| 1 MLOps, API and live delivery | 0 | Needs the repo, config and model client |
| 2 Evaluation base | 1 | Logs to MLflow, runs on Colab and Kaggle profiles |
| 3 Ingestion | 2 | Tested against the frozen test sets |
| 4 Charts and figures | 3 | Needs parsed figures and page images |
| 5 Retrieval | 3, 4 | Needs chunks and figure descriptions |
| 6 Grounded answers | 5 | Needs ranked evidence |
| 7 Agents and memory | 6 | Routes call the answer pipeline |
| 8 Web search | 7 | A route in the agent graph. Uses the claim check from 6 |
| 9 Summaries | 6, 7 | Uses section structure and the router |
| 9A Knowledge graph, ontology and GraphRAG | 3, 5, 6, 7 | Uses parsed chunks, search, grounding and the router |
| 9B Notebooks and study tools | 9, 9A | Uses summaries and the graph |
| 10 Extraction | 3, 7 | Uses parsed documents and the router |
| 11 Calculations | 3, 7 | Uses parsed tables and the router |
| 12 Security | 7 to 11, 9A, 9B | Protects all routes |
| 13 API hardening, UI, MCP | 1, 12 | Freezes the API built since Phase 1 |
| 14 Audio | 3, 5, 13 | New input type through the same pipeline and UI |
| 15 Company package | 13 | Packages the hardened system |
| 16 Handover | All | Final check |


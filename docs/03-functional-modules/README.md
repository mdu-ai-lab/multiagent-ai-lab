# Functional modules

| Field | Value |
|---|---|
| Purpose | Index of planned modules |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Functional requirements](../01-requirements/functional-requirements.md), [System architecture](../04-architecture/system-architecture.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Module | Purpose | Phase |
|---|---|---|
| [Ingestion](ingestion.md) | Turn uploaded files into structured elements and page images | Phase 3 |
| [Visual content](visual-content.md) | Make charts, figures and tables searchable | Phase 4 |
| [Retrieval](retrieval.md) | Find the right evidence fast | Phase 5 |
| [Grounded answers](grounded-answers.md) | Produce cited answers or refuse | Phase 6 |
| [Agents and memory](agents-and-memory.md) | Send each request to the right route and remember the chat | Phase 7 |
| [Web search](web-search.md) | Bring in online information on request | Phase 8 |
| [Summaries](summaries.md) | Summaries that miss nothing | Phase 9 |
| [Extraction](extraction.md) | Reliable JSON from documents | Phase 10 |
| [Calculations](calculations.md) | Exact numbers and plots from tables | Phase 11 |
| [Audio](audio.md) | Questions over recordings | Phase 14 |
| [API, UI and MCP](api-ui-mcp.md) | One contract for every client | Phases 1 and 13 |
| [Knowledge graph and GraphRAG](knowledge-graph.md) | Answer relationship and whole-corpus questions from an ontology-based knowledge graph | Phase 9A (D17, D18) |
| [Notebooks and study tools](notebooks.md) | Topic workspaces with study outputs | Phase 9B (D19) |
| [Evaluation](evaluation.md) | Measure quality honestly | Phase 2 |
| [Delivery and operations](delivery-and-operations.md) | CI, live site, demo, backup and monitoring | Phases 0 and 1 |

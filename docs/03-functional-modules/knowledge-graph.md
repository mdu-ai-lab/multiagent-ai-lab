# Module: Knowledge graph and GraphRAG

| Field | Value |
|---|---|
| Purpose | Specification of the knowledge graph and graphrag module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Answer relationship and whole-corpus questions from an ontology-based knowledge graph |
| Actors | Member, worker |
| Functional requirements | FR-KG-001 to FR-KG-004 |
| Business rules | BR-KG-001, BR-ACC-001, BR-KEEP-001 |
| Planned files | ontology.py, kg.py, graphrag.py, configs/ontology/ |
| Models and tools | LinkML, LightRAG or own graph with NetworkX (chosen in 9A.3), main model |
| Data entities | Graph entities and relations with source page (graph store on the SSD, format chosen in 9A.3) |
| API endpoints | Through the chat endpoint (graph route) |
| Input validation | Extraction output forced into the ontology JSON schema |
| Expected outputs | Entities and relations with sources. Answers with page citations |
| Error conditions | Wrong or unsupported facts removed by claim check. Graph route off where it does not help |
| Events and notifications | Graph build job status |
| Security considerations | Cross-collection leaks through merged entities. False relations from poisoned documents |
| Testing requirements | Extraction precision on 50 hand-checked facts, engine comparison, hybrid vs GraphRAG test |
| Acceptance criteria | AT-9A.1 to AT-9A.5 |
| Plan and paper references | Phase 9A (D17, D18) |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

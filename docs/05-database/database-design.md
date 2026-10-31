# Database design

| Field | Value |
|---|---|
| Purpose | Planned data stores and how they are used |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [ER diagram](../05-database/er-diagram.md), [Data dictionary](../05-database/data-dictionary.md), [ADR-005](../04-architecture/architecture-decision-records/ADR-005.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

No database, model or migration exists yet. This is the planned design.

## Data stores

| Store | Holds | Owner module | Source |
|---|---|---|---|
| SQLite through SQLAlchemy (PostgreSQL by config in Phase 15) | Users, collections, access, documents, versions, elements, jobs | db.py | ADR-005, 3.4, 12.4 |
| LangGraph checkpointer (SQLite, Postgres later) | Chat threads and memory. Schema owned by LangGraph, not by us | memory.py | 7.5, 15.3 |
| Qdrant | Chunk and page-image vectors with payload | index.py | ADR-004, 5.2 |
| MLflow | Runs, prompts, pipeline versions, traces, feedback | tracing.py | ADR-006, 13.4 |
| Files on the SSD | Uploaded originals, page images, results | worker.py | Section 6.3 |
| Knowledge graph store | Entities and relations with source pages, community summaries. Format chosen in 9A.3 (LightRAG local storage or NetworkX files) | kg.py | ADR-017, 9A.2, 9A.3 |
| Ontology files | LinkML YAML in configs/ontology/, generating Pydantic models and an OWL file. Versioned in Git | ontology.py | ADR-018, 9A.1 |

## Discrepancy

WORK_PLAN.md section 6.3 (storage layout) and section 6.4 (backup layers) do not yet list the knowledge graph store or notebook data. Their backup layer: REQUIRES CONFIRMATION.

## Migration strategy

Alembic with SQLAlchemy, decided in step 0.1 (WORK_PLAN.md D25). Settings are in pyproject.toml ([tool.alembic]) and the migration files in migrations/. The database URL comes from src/mrag/config.py. No tables or migrations exist yet. The SQLite file is data/app.db (ignored by Git). Its backup layer is decided in step 0.6.

## Not created as separate documents

indexes-and-performance.md and migration-strategy.md are not created. No tables or queries exist, so index advice would be guesswork. The migration tool is open (above).

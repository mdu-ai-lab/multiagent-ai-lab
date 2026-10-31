# ER diagram

| Field | Value |
|---|---|
| Purpose | Proposed relational entities |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Data dictionary](../05-database/data-dictionary.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

PROPOSED. Entity and field names are suggestions built from WORK_PLAN.md steps 3.1, 3.4, 3.5 and 12.4. They are finalised when those steps start.

```mermaid
erDiagram
  USER ||--o{ COLLECTION_ACCESS : has
  COLLECTION ||--o{ COLLECTION_ACCESS : grants
  COLLECTION ||--o{ DOCUMENT : contains
  DOCUMENT ||--o{ DOCUMENT_VERSION : has
  DOCUMENT_VERSION ||--o{ ELEMENT : contains
  DOCUMENT_VERSION ||--o{ JOB : processed_by
  USER ||--o{ NOTEBOOK : owns
  NOTEBOOK }o--o{ DOCUMENT : uses_as_source
  NOTEBOOK ||--o{ NOTE : contains
  USER {
    id id
    string name
  }
  COLLECTION {
    id id
    string name
  }
  COLLECTION_ACCESS {
    id user_id
    id collection_id
  }
  DOCUMENT {
    id id
    id collection_id
    string file_name
  }
  DOCUMENT_VERSION {
    id id
    id document_id
    int version
    string sha256
  }
  ELEMENT {
    id id
    id version_id
    int page
    string heading_path
    string box
    string type
    text text
  }
  JOB {
    id id
    id version_id
    string status
    string error
  }
  NOTEBOOK {
    id id
    string name
  }
  NOTE {
    id id
    id notebook_id
    text text
    string citations
  }
```

Chat threads (LangGraph), vectors (Qdrant), the knowledge graph (graph store) and traces (MLflow) live in their own stores and are not drawn here. NOTEBOOK and NOTE come from step 9B.1. Their storage is not decided: REQUIRES CONFIRMATION.

# ER diagram

| Field | Value |
|---|---|
| Purpose | Proposed relational entities |
| Status | Proposed |
| Last updated | 2026-11-15 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Data dictionary](../05-database/data-dictionary.md) |

> Implementation status: see docs/WORK_PLAN.md, section 1 (current state). Test results are in docs/HANDOVER.md.

PROPOSED. Entity and field names are suggestions built from WORK_PLAN.md steps 3.1, 3.4, 3.5 and 12.4. They are finalised when those steps start. USER, SESSION, CHAT, MESSAGE, FEEDBACK and AUDIT_LOG exist since step 1.10 (src/mrag/db.py). The other entities are still proposed.

```mermaid
erDiagram
  USER ||--o{ SESSION : logs_in_with
  USER ||--o{ CHAT : owns
  SESSION ||--o{ CHAT : owns_guest_chats
  CHAT ||--o{ MESSAGE : contains
  USER |o--o{ FEEDBACK : sends
  USER |o--o{ AUDIT_LOG : acts_in
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
    string email
    string name
    string role
  }
  SESSION {
    id id
    string token_hash
    id user_id
    datetime expires_at
  }
  CHAT {
    uuid id
    id user_id
    id session_id
    string title
  }
  MESSAGE {
    id id
    uuid chat_id
    string role
    text content
    string status
  }
  FEEDBACK {
    id id
    id user_id
    string kind
    text message
  }
  AUDIT_LOG {
    id id
    id admin_id
    string action
    string target
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

The state of running requests (LangGraph checkpointer), vectors (Qdrant), the knowledge graph (graph store) and traces (MLflow) live in their own stores and are not drawn here. NOTEBOOK and NOTE come from step 9B.1. Their storage is not decided: REQUIRES CONFIRMATION.

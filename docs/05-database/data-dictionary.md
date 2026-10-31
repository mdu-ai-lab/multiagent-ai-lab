# Data dictionary

| Field | Value |
|---|---|
| Purpose | Proposed fields and their meaning |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [ER diagram](../05-database/er-diagram.md), [Relationships and constraints](../05-database/relationships-and-constraints.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

PROPOSED. Only fields named or clearly implied in WORK_PLAN.md are listed. Types, timestamps and audit fields: REQUIRES CONFIRMATION.

| Entity | Field | Meaning | Source |
|---|---|---|---|
| user | id, name | A person who logs in | 12.4, 13.1 |
| user | password hash | Hashed password. Hash method REQUIRES CONFIRMATION | 13.1 |
| collection | id, name | A group of documents with shared access | 12.4 |
| collection_access | user_id, collection_id | Which user may see which collection | 12.4 |
| document | id, collection_id, file name | One uploaded file across its versions | 3.5 |
| document_version | id, document_id, version, sha256 | One exact file content. Older versions hidden from search | 3.5 |
| element | id, version_id, page, heading path, box, type, text | One parsed part of a page | 3.4 |
| element | model-generated flag | Marks vision-model descriptions | 4.1 |
| element | time range | Start and end time for audio chunks | 14.2 |
| job | id, version_id, status, error | Status: queued, parsing, indexing, done, failed | 3.1 |
| Qdrant point | vectors and payload: collection, file, version, page, type, heading | Searchable chunk or page image | 5.2 |
| notebook | id, name, owner, chosen sources | Workspace on one topic | 9B.1 |
| note | id, notebook_id, text, citations | Saved answer or note with its citations | 9B.1 |
| graph entity and relation | type from the ontology, name and aliases, source chunk, file and page | Knowledge graph fact (graph store) | 9A.2 |

## Sensitive data

Element text and uploaded files may contain personal data. They stay on the Mac (BR-PRIV-001). Personal data is masked in traces, logs, MLflow and exports (NFR-SEC-006). Retention period: REQUIRES CONFIRMATION.

# Relationships and constraints

| Field | Value |
|---|---|
| Purpose | Proposed integrity rules |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Data dictionary](../05-database/data-dictionary.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| ID | Rule | Reason | Status |
|---|---|---|---|
| DBC-001 | One document version per (document, sha256) | Duplicate upload adds nothing (3.5) | Proposed |
| DBC-002 | Deleting a document removes its versions, elements, jobs and Qdrant points | "Delete removes everything from that file" (3.5) | Proposed |
| DBC-003 | Every element has a page or a time range | Citations need a location (3.4, 14.2) | Proposed |
| DBC-004 | Job status is one of the 5 listed values | 3.1 | Proposed |
| DBC-005 | Access rows link an existing user and collection | 12.4 | Proposed |
| DBC-006 | Every graph entity and relation has a source page | 9A.2 | Proposed |
| DBC-007 | Graph entity and relation types must exist in the ontology | 9A.1, 9A.2 | Proposed |
| DBC-008 | A notebook's sources must be in collections the user can access | 9B.1 | Proposed |

Deleting from Qdrant is outside the SQL transaction, so DBC-002 needs a checked clean-up step. Design: REQUIRES CONFIRMATION in step 3.5.

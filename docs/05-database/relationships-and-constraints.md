# Relationships and constraints

| Field | Value |
|---|---|
| Purpose | Proposed integrity rules |
| Status | Proposed |
| Last updated | 2026-11-15 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Data dictionary](../05-database/data-dictionary.md) |

> Implementation status: see docs/WORK_PLAN.md, section 1 (current state). Test results are in docs/HANDOVER.md.

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
| DBC-009 | An email belongs to one account only | Sign-up must not create two accounts for one address (1.10). auth.py saves emails in lower case | Implemented (src/mrag/db.py) |
| DBC-010 | A chat has exactly one owner: a user or a guest's session | Guest chats are deleted with the session (D49) | Implemented (src/mrag/db.py) |
| DBC-011 | Deleting a user deletes their sessions, chats and messages. Feedback and the admin activity log stay without the link | A deleted account leaves no chats behind. Admin actions stay traceable (D49) | Implemented (src/mrag/db.py) |
| DBC-012 | User role, message role, message status and feedback kind are one of their listed values | A bug in the code cannot store an unknown role (1.10) | Implemented (src/mrag/db.py) |
| DBC-013 | Every time is stored in UTC | One clock for sessions and time limits on every database (1.10) | Implemented (src/mrag/db.py) |

Deleting from Qdrant is outside the SQL transaction, so DBC-002 needs a checked clean-up step. Design: REQUIRES CONFIRMATION in step 3.5.

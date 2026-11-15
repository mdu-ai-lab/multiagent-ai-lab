# Data dictionary

| Field | Value |
|---|---|
| Purpose | Proposed fields and their meaning |
| Status | Proposed |
| Last updated | 2026-11-15 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [ER diagram](../05-database/er-diagram.md), [Relationships and constraints](../05-database/relationships-and-constraints.md) |

> Implementation status: see docs/WORK_PLAN.md, section 1 (current state). Test results are in docs/HANDOVER.md.

PROPOSED. Only fields named or clearly implied in WORK_PLAN.md are listed. Types, timestamps and audit fields: REQUIRES CONFIRMATION. The tables of step 1.10 exist in src/mrag/db.py. The migration d566b5bd752c builds them. All times are stored in UTC.

| Entity | Field | Meaning | Source |
|---|---|---|---|
| users | id, email (unique), name, role (member or admin), blocked, settings (theme, language and chat settings of the page), created_at, last_login_at | A person who logs in | 1.10, 12.4 |
| users | password_hash | Argon2id hash with its own salt and settings | 1.10, D49 |
| sessions | id, token_hash (SHA-256 of the cookie token), user_id (empty for a guest), csrf_token, remember, guest_messages, created_at, last_seen_at, expires_at | The session of one browser | 1.10, D49 |
| chats | id (random UUID), user_id or session_id (exactly one of them), title, created_at, updated_at | A saved chat. A guest's chat is deleted with the session | 1.10, D49 |
| messages | id, chat_id, role (user or assistant), content, status (done, stopped or failed), created_at | One turn of a chat, read in order by harness/memory.py | 1.10, D43 |
| feedback | id, user_id (empty after the user is deleted), kind (problem, idea or other), message, done, created_at | Feedback sent from the page | 1.10 |
| app_settings | key, value | Guest mode, the guest message limit and sign-up, changed by an admin | 1.10, D49 |
| audit_log | id, admin_id (empty after the admin is deleted), admin_label, action, target, details, created_at | Every admin action | 1.10, D49 |
| guest_daily | day, messages | Guest messages per day for the admin dashboard | 1.10 |
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

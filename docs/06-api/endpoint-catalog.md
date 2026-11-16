# Endpoint catalog

| Field | Value |
|---|---|
| Purpose | Planned endpoints by phase |
| Status | Proposed |
| Last updated | 2026-11-16 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [API standards](../06-api/api-standards.md), [Modules](../03-functional-modules/README.md) |

> Implementation status: see docs/WORK_PLAN.md, section 1 (current state). Test results are in docs/HANDOVER.md.

The endpoints below exist in src/mrag/api.py (WORK_PLAN.md D45, D49). They are experimental until Phase 13 freezes the API. "Token" means the header X-CSRF-Token with the token of the caller's session.

| Method | Path | Purpose | Auth | Phase | Status |
|---|---|---|---|---|---|
| GET | /v1/health | Service is up | None | 1.6 | Implemented (experimental) |
| GET | /v1/version | Code and pipeline version | None | 1.6 | Implemented (experimental) |
| POST | /v1/auth/login | Log in. A new session replaces the browser's session. Every failed login gives the same answer | Token of the page's session | 1.10 | Implemented (experimental) |
| POST | /v1/auth/signup | Create a member account and log in. Only while an admin allows sign-up | Token of the page's session | 1.10 | Implemented (experimental) |
| POST | /v1/auth/logout | End the session of this browser | Token | 1.10 | Implemented (experimental) |
| GET | /v1/models | Models in the active profile, read from configs/models.yaml without a model call | Login | 1.6, 1.10 | Implemented (experimental) |
| POST | /v1/chat | Chat and file questions, streamed. Starts a saved chat or continues one (chat_id). Events: chat, delta, then done or error | Login or a guest session while guest mode is on. Token | 1.6, 1.10, 6, 7, 8 | Implemented (experimental) |
| GET | /v1/chats | The caller's chats, newest first | Login or a guest session while guest mode is on | 1.10 | Implemented (experimental) |
| GET | /v1/chats/{chat_id} | One chat with its messages. Each answer also as safe HTML made from its Markdown | Login or a guest session while guest mode is on | 1.10 | Implemented (experimental) |
| PATCH | /v1/chats/{chat_id} | New title of 1 to 80 characters | Login or a guest session while guest mode is on. Token | 1.10 | Implemented (experimental) |
| DELETE | /v1/chats/{chat_id} | Delete one chat with its messages | Login or a guest session while guest mode is on. Token | 1.10 | Implemented (experimental) |
| DELETE | /v1/chats | Delete all chats of the caller | Login or a guest session while guest mode is on. Token | 1.10 | Implemented (experimental) |
| PATCH | /v1/me | Change the own name. Answers the new name and initials | Login. Token | 1.10 | Implemented (experimental) |
| PATCH | /v1/me/preferences | Theme, language, Enter sends, example questions and the hidden sidebar | Login. Token | 1.10 | Implemented (experimental) |
| POST | /v1/me/password | Change the password. Other logins end and this browser gets a new session | Login. Token | 1.10 | Implemented (experimental) |
| GET | /v1/me/export | All own chats as a JSON file | Login | 1.10 | Implemented (experimental) |
| POST | /v1/me/delete | Delete the own account with its chats. Needs the password. The last admin cannot | Login. Token | 1.10 | Implemented (experimental) |
| POST | /v1/feedback | Send feedback: problem, idea or other | Login. Token | 1.10 | Implemented (experimental) |

A chat of someone else answers 404 like a chat that does not exist, so no chat ID is ever confirmed.

The chat page itself (/, /login and /signup) and its files in /static come from src/mrag/ui.py in the same app. They are not part of the API documentation.

## Capabilities planned without fixed paths

| Capability | Phase | Path |
|---|---|---|
| Upload a file | 3.1 | REQUIRES CONFIRMATION |
| Job status | 3.1 | REQUIRES CONFIRMATION |
| Summaries | 9 | REQUIRES CONFIRMATION |
| Graph questions | 9A.4 | Through POST /v1/chat (router picks the graph route) |
| Build or rebuild a collection's graph | 9A.2 | REQUIRES CONFIRMATION |
| Notebooks, notes and study outputs | 9B | REQUIRES CONFIRMATION |
| Extraction and export | 10 | REQUIRES CONFIRMATION |
| Admin | 1.10 | Paths set when they are built |
| Answer ratings | 13.4 | Path set in 13.4 |

Rule A: each feature phase adds its endpoint when the feature is built. This catalog is updated then.

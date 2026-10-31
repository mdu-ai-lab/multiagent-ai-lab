# Use cases

| Field | Value |
|---|---|
| Purpose | Main planned user journeys |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [User flows](../08-ui-ux/user-flows.md), [Functional requirements](../01-requirements/functional-requirements.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| ID | Use case | Actor | Main requirements |
|---|---|---|---|
| UC-01 | Upload a file and wait for indexing | Member | FR-ING-001 to 006 |
| UC-02 | Ask a question and get a cited answer | Member | FR-RET-*, FR-QA-001 to 005 |
| UC-03 | Get "not found" when the files lack the answer | Member | FR-QA-004 |
| UC-04 | Compare two documents | Member | FR-QA-006 |
| UC-05 | Ask with web search on | Member | FR-WEB-001 to 003 |
| UC-06 | Summarise a long document | Member | FR-SUM-001 |
| UC-07 | Summarise many reviews | Member | FR-SUM-002 |
| UC-08 | Extract JSON from documents and export | Member | FR-EXT-001 to 004 |
| UC-09 | Calculate or plot from a table | Member | FR-CALC-001 to 003 |
| UC-10 | Ask about an audio recording | Member | FR-AUD-001 |
| UC-11 | Use the platform from another AI tool | MCP client | FR-MCP-001 |
| UC-12 | Rate an answer | Member | FR-FBK-001 |
| UC-13 | Try the public demo | Demo visitor | FR-OPS-002 |
| UC-14 | Follow project progress | Anyone | FR-OPS-001 |
| UC-15 | Manage users and collections | Platform admin | FR-ADM-001 (REQUIRES CONFIRMATION) |
| UC-16 | Ask how people, places or concepts relate across documents | Member | FR-KG-004 |
| UC-17 | Work on a topic in a notebook and save notes | Member | FR-NB-001 |
| UC-18 | Generate a study guide, FAQ, briefing, flashcards or quiz | Member | FR-NB-002 |
| UC-19 | Explore a mind map of a notebook | Member | FR-NB-003 |

## Example: UC-02

1. The member types a question in a chat with chosen files.
2. The router sends it to document Q&A (FR-AGT-001).
3. Search runs with the member's collection filter (BR-ACC-001).
4. The answer streams with [S#] citations (FR-QA-001).
5. The claim check removes or marks unsupported sentences (FR-QA-003).
6. The member opens a citation and sees the highlighted box on the page (FR-QA-005).

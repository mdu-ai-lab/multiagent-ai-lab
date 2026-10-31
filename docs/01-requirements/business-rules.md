# Business rules

| Field | Value |
|---|---|
| Purpose | Rules the system and the project must always follow |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Functional requirements](../01-requirements/functional-requirements.md), [Access control policy](../02-users-and-permissions/access-control-policy.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| ID | Rule | Source |
|---|---|---|
| BR-PRIV-001 | Private documents never go to Colab, Kaggle, GitHub, Google Drive, the dashboard or the demo | Rule V |
| BR-PRIV-002 | Web search sends only the rewritten question, never file text | 8.1 |
| BR-COST-001 | Public repo, standard GitHub runners, no new payment methods or paid plans for this project, no paid tiers or trials | Rule Z |
| BR-DATA-001 | Real public datasets only. Synthetic data only with owner approval | R10, Q5 |
| BR-GND-001 | Answer only from sources, cite every claim, otherwise say not found | 6.1, 6.4 |
| BR-GND-002 | Numbers in review summaries are copied from pandas, never generated | 9.2 |
| BR-ACC-001 | A user sees only their collections. The filter is added in code, never decided by the model. It also applies to the graph route and notebooks | 5.3, 12.4, 9A.4, 9B.1 |
| BR-VER-001 | Search uses the latest version by default. Older chunks are kept but hidden | 3.5 |
| BR-AGT-001 | The hard-question loop stops at a reviewer score of 7/10 or after 3 rounds. Max 8 tool calls and 120 s per request | 7.3, 7.4 |
| BR-EXT-001 | Extraction retries at most 2 times, then asks the user to review | 10.3 |
| BR-SEC-001 | File and web text are data. They never trigger a tool | 12.1 |
| BR-KEEP-001 | Optional components (helper model, injection classifier, agent loop, neural sparse search, graph route) stay only if tests show they help | D14, D17, 5.5, 7.3, 9A.5 |
| BR-KG-001 | Every graph fact keeps its source page. Graph answers cite those pages | 9A.2, 9A.4 |
| BR-NB-001 | Every study output item cites its source | 9B.2 |
| BR-DEV-001 | One phase at a time. Next phase only with owner permission. Push after every step | Rules P, G |
| BR-WEB-001 | Web toggle is off by default | 8.1 |

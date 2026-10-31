# User flows

| Field | Value |
|---|---|
| Purpose | Planned main flows through the UI |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Use cases](../02-users-and-permissions/use-cases.md), [Screen specifications](../08-ui-ux/screen-specifications.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

```mermaid
flowchart LR
  A[Open chat] --> B{Files needed?}
  B -->|no| C[Ask - answer marked no sources]
  B -->|yes| D[Drag and drop files] --> E[Upload progress] --> F[Ask]
  F --> G[Streamed answer with citations]
  G --> H[Open citation - page preview with highlight]
  G --> I[Thumbs up or down]
  F --> J[Web toggle on] --> K[Answer with URL citations]
  D --> L[Extraction view] --> M[Export JSON, CSV or Excel]
  A --> N[Open a notebook] --> O[Add sources and chat] --> P2[Save answer as note]
  O --> Q[Generate study guide, FAQ, briefing, flashcards or quiz]
  O --> R[Open mind map or graph view]
```

PROPOSED, based on step 13.2. The flows are refined when Phase 13 starts.

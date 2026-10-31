# Performance testing

| Field | Value |
|---|---|
| Purpose | Planned performance measurements |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Non-functional requirements](../01-requirements/non-functional-requirements.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Test | Target | Where | Step |
|---|---|---|---|
| Peak RAM with main + embedding + reranker | < 13 GB | Mac | 0.4 |
| Words per second, time to first word | Recorded | Mac | 0.4 |
| Search latency p50 | ≤ 2 s | Mac | 5.5 |
| Load: 10 users at once | Speed and errors reported | Kaggle GPU | 15.4 |
| Graph extraction time and model calls per document | Recorded | Mac and Colab | 9A.2, 9A.5 |
| Answer latency | Recorded in monitoring view. Target REQUIRES CONFIRMATION | Mac | 13.4 |

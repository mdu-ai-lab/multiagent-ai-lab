# Performance testing

| Field | Value |
|---|---|
| Purpose | Planned performance measurements |
| Status | Proposed |
| Last updated | 2026-11-11 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Non-functional requirements](../01-requirements/non-functional-requirements.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Test | Target | Where | Step |
|---|---|---|---|
| Peak RAM with main + embedding + reranker | < 13 GB | Mac | 0.4 |
| Words per second, time to first word | Recorded | Mac | 0.4 |
| Search latency p50 | ≤ 2 s | Mac | 5.5 |
| Load: 10 users at once | Speed and errors reported | Kaggle GPU | 15.4 |
| Graph extraction time and model calls per document | Recorded | Mac and Kaggle | 9A.2, 9A.5 |
| Answer latency | Recorded in monitoring view. Target REQUIRES CONFIRMATION | Mac | 13.4 |

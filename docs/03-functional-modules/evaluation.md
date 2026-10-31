# Module: Evaluation

| Field | Value |
|---|---|
| Purpose | Specification of the evaluation module |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Modules index](../03-functional-modules/README.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Item | Detail |
|---|---|
| Purpose | Measure quality honestly |
| Actors | Owner |
| Functional requirements | FR-EVAL-001 to FR-EVAL-003 |
| Business rules | BR-DATA-001 |
| Planned files | eval_data.py, eval_metrics.py, eval_run.py, judge.py |
| Models and tools | MLflow, HF datasets, Gemma 4 judge |
| Data entities | Test sets (JSONL) |
| API endpoints | — |
| Input validation | Frozen test sets |
| Expected outputs | Metrics with CIs in MLflow and results/ |
| Error conditions | — |
| Events and notifications | — |
| Security considerations | Judge bias |
| Testing requirements | Rerun gives identical numbers, human check |
| Acceptance criteria | AT-2.1 to AT-2.5 |
| Plan and paper references | Phase 2 |
| Permissions | See [role permission matrix](../02-users-and-permissions/role-permission-matrix.md) |
| Current implementation status | Not implemented |
| Known gaps | Exact endpoint paths and storage details are decided when the phase starts |

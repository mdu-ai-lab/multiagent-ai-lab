# Monitoring and logging

| Field | Value |
|---|---|
| Purpose | How the platform will be watched |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Incident response](../10-deployment-and-operations/incident-response.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| What | Tool | Step |
|---|---|---|
| Every agent step and model call with time and tokens | MLflow tracing | 1.2 |
| Fallbacks | Logged in the trace | 7.4 |
| Latency, errors, fallbacks, low-rated answers | Local monitoring view | 13.4 |
| User feedback | Saved to the trace | 13.4 |
| Live dashboard and demo up | health.yml opens an issue | 1.9 |
| Mac resources | results/p0_resources.csv | 0.4 |

Personal data is masked in traces and logs from Phase 12 (12.3). Before then, traces may contain document text and stay on the Mac. Alerting beyond GitHub issues: not planned.

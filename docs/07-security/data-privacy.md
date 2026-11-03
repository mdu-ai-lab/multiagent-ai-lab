# Data privacy

| Field | Value |
|---|---|
| Purpose | How private and personal data is handled |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Business rules](../01-requirements/business-rules.md), [Backup and recovery](../10-deployment-and-operations/backup-and-recovery.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Data | Where it may live | Where it may never go | Rule |
|---|---|---|---|
| Private documents and their index | Mac SSD | Colab, Kaggle, GitHub, dashboard, demo | BR-PRIV-001 |
| Questions with web search on | Mac and the search engine (rewritten question only) | — | BR-PRIV-002 |
| Traces and logs | Mac (MLflow) | Online, unless masked and exported as results | NFR-SEC-006 |
| Public datasets and results | Mac, Colab, Kaggle, GitHub, dashboard | — | BR-DATA-001 |
| Knowledge graphs built from private documents | Mac | Colab, Kaggle, GitHub, demo | BR-PRIV-001 |
| Notebooks and notes | Mac | Same as private documents | BR-PRIV-001 |

Backup: the whole project on the SSD is copied to the owner's Google Drive (D35). Retention and deletion periods: REQUIRES CONFIRMATION. No GDPR compliance is claimed.

# Constraints and assumptions

| Field | Value |
|---|---|
| Purpose | Fixed limits and open assumptions that shape the design |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [SRS](../01-requirements/srs.md), [Risk register](../12-project-management/risk-register.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

## Constraints

| ID | Constraint | Source |
|---|---|---|
| CON-001 | Zero cost everywhere | Rule Z |
| CON-002 | Main machine: MacBook Air M2, 16 GB RAM, project on an external 2 TB SSD | Section 6 |
| CON-003 | Free cloud GPU only: Colab free (main), Kaggle free (backup) | D10 |
| CON-004 | Private documents stay on the Mac | Rule V |
| CON-005 | Google Drive: the owner's existing 2 TB plan | Section 7 |
| CON-006 | ZeroGPU Spaces only on the personal Hugging Face account (organizations need a paid plan) | D16 |
| CON-008 | Python 3.12, uv, flat modules in src/<package>/ | Rule C2 |

## Assumptions (each needs confirmation)

| ID | Assumption | Confirm by |
|---|---|---|
| ASM-001 | Free-tier limits stay as checked on 28 Oct 2026 | Re-check in 1.7 and 1.8 |
| ASM-002 | Qwen3.5-9B fits the Mac within the RAM target | Step 0.4 |
| ASM-003 | Qwen3.8-27B runs on Kaggle 2 x T4 | Step 1.5 |
| ASM-004 | Qwen3.5-9B runs on ZeroGPU through Transformers | Step 1.8 |
| ASM-005 | The Hugging Face account is over 30 days old with a verified email | Q3 |
| ASM-006 | smolagents WebSearchTool works without a key or payment | Step 8.1 |
| ASM-007 | v1 is evaluated in English. Swedish is open | Q6 |
| ASM-008 | SPACE licence allows use | Q4 |
| ASM-009 | LinkML licence allows use | Step 9A.1 |
| ASM-010 | LightRAG works with our model server and embeddings | Step 9A.3 |
| ASM-011 | MuSiQue licence is CC BY 4.0 (one source says CC BY-SA 4.0) | Step 2.1 |
| ASM-012 | "Knowledge" means the knowledge base in R31 | Q11 |

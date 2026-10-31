# Deployment architecture

| Field | Value |
|---|---|
| Purpose | Where each part runs in each profile |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Deployment guide](../10-deployment-and-operations/deployment-guide.md), [Environment configuration](../10-deployment-and-operations/environment-configuration.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

```mermaid
flowchart TB
  subgraph Mac[MacBook Air M2 - external SSD]
    DK[Docker: Qdrant, MLflow, code sandbox]
    NT[Native: llama.cpp + llama-swap, worker, API, UI]
    SQ[(SQLite)]
  end
  subgraph Cloud[Free cloud - public data only]
    CL[Colab T4: vLLM jobs, public knowledge graphs]
    KG[Kaggle 2 x T4: 27B tests, load test]
    ZG[ZeroGPU Space: demo]
    GP[GitHub Pages: dashboard]
    GA[GitHub Actions: CI/CD]
  end
  subgraph Company[Company Linux GPU server - Phase 15, PROPOSED]
    VL[vLLM] --- SV[Platform containers] --- PS[(PostgreSQL)]
  end
```

| Profile | Runs | Data allowed |
|---|---|---|
| Mac | Full platform | Private and public |
| GPU | Batch jobs | Public only |
| Demo | Demo app | Public samples |
| CI | Tests | Public fixtures |
| Company server | Full platform in containers | Company data inside its network |

Model servers run natively on the Mac because containers there cannot use the Metal GPU (WORK_PLAN.md section 6, ADR-002).

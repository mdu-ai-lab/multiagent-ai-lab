# Risk register

| Field | Value |
|---|---|
| Purpose | Project, technical and security risks |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Threat model](../07-security/threat-model.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

Risks RISK-001 to RISK-020 are copied from WORK_PLAN.md section 14. Security findings SF-01 to SF-11 are in the [threat model](../07-security/threat-model.md).

| ID / Risk | Impact | Mitigation |
|---|---|---|
| RISK-001  A free tier changes (GitHub, Hugging Face, Colab, Kaggle, Google Drive) | Live site, demo or GPU access stops | The full platform always runs on the Mac. Re-check limits in 1.7 and 1.8. Health checks in 1.9 |
| RISK-002  Colab has no free GPU when needed | Delays | Kaggle backup. Jobs are resumable |
| RISK-003  16 GB RAM pressure on the Mac | Slow or crashes | llama-swap unloading, one large model at a time, measured in 0.4 |
| RISK-004  Fanless M2 throttling during long jobs | Slow ingestion | Resumable jobs, overnight runs, Colab for public data |
| RISK-005  SSD unavailable or damaged | Lost local work | Git + Drive backup + restore test (6.4). Models and datasets re-created from pinned versions |
| RISK-006  Google Drive fills up (2 TB) | Backup and email stop | Monthly usage check |
| RISK-007  Sync conflicts between SSD, Drive and Colab | Lost or duplicated files | Git as source of truth, one-way backup, unique result names, remote branches (6.4) |
| RISK-008  9B model weaker than large APIs | Lower accuracy | Strong retrieval, constrained output, claim check, refusal. Honest reporting |
| RISK-009  Agent loop hurts faithfulness or speed | Worse answers | Gated loop and ablation (7.3) |
| RISK-010  Local judge bias | Misleading scores | Other-family judge, human check, deterministic metrics first (2.5) |
| RISK-011  Dataset licence or fit | Can't use a dataset | Checked in 2.1, replaced if needed |
| RISK-012  Hidden instructions in documents or web pages | Data leak or misuse | Phase 12, sandbox, no tools from document text |
| RISK-013  Model or package supply chain | Tampered files | Pinned revisions and hashes, uv.lock, pip-audit, Dependabot |
| RISK-014  Fast-moving tools | Breaking upgrades | Pin everything. Upgrade only through the CI evaluation gate |
| RISK-015  Scope creep | Never finish | Non-goals list, phase gates |
| RISK-016  Graph extraction is slow on the Mac and costs many model calls | Long ingestion | Graph is optional per collection. Large public corpora on Colab. Time and calls measured in 9A.5 |
| RISK-017  The main model extracts wrong entities or relations | Wrong graph answers | Ontology-constrained JSON output, source citation for every graph fact, claim check, test in 9A.5 |
| RISK-018  GraphRAG does not beat hybrid RAG | Wasted effort | Kept only where tests show it helps (D17) |
| RISK-019  Docker Desktop licence in companies | Unexpected cost for a company | Docker Engine on Linux servers (15.5) |
| RISK-020  Context lost between chats | Wrong decisions repeated | This file, decision log, end-of-chat checklist |

# Architecture decision records

| Field | Value |
|---|---|
| Purpose | Index of decisions taken from the WORK_PLAN.md decision log |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../../WORK_PLAN.md) v1.9 |
| Related documents | [System architecture](../../04-architecture/system-architecture.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

ADRs are copied from WORK_PLAN.md section 4.1 without changes in meaning. New decisions are added there first, then here.

| ADR | Decision |
|---|---|
| [ADR-001](ADR-001.md) | Platform runs locally. Private documents stay on the Mac |
| [ADR-002](ADR-002.md) | Main local runtime: llama.cpp + llama-swap (GGUF, Metal) |
| [ADR-003](ADR-003.md) | Orchestration: LangGraph. Code agent and web tool: smolagents |
| [ADR-004](ADR-004.md) | Search database: Qdrant (Docker on Mac, in-process mode in the demo) |
| [ADR-005](ADR-005.md) | App database: SQLite through SQLAlchemy. Postgres by config in Phase 15 |
| [ADR-006](ADR-006.md) | MLflow (local) for experiments, prompt and pipeline versions, traces and feedback |
| [ADR-007](ADR-007.md) | CI on GitHub Actions (public repo, standard runners). CD for dashboard, demo and images |
| [ADR-008](ADR-008.md) | API-first: service.py + FastAPI skeleton in Phase 1. Hardening in Phase 13 |
| [ADR-009](ADR-009.md) | Live dashboard on GitHub Pages. Live demo on a free Hugging Face ZeroGPU Space (Gradio) |
| [ADR-010](ADR-010.md) | Cloud GPU: Google Colab free is the main cloud GPU. Kaggle free is the backup and the place for jobs needing 2 x T4 (32 GB) |
| [ADR-011](ADR-011.md) | GPU profile model: Qwen3.5-9B at higher precision on a Colab T4. Qwen3.8-27B tested on Kaggle 2 x T4 and used only if it runs well |
| [ADR-012](ADR-012.md) | Code and docs live in Git (GitHub = source of truth). Google Drive holds a one-way, versioned backup of non-Git files plus a Colab inbox. No two-way folder sync |
| [ADR-013](ADR-013.md) | Models, public datasets, venvs and indexes are not backed up. They are re-created from pinned versions |
| [ADR-014](ADR-014.md) | Helper model Qwen3.5-2B, speech-to-text (late phase), MCP and an injection classifier are included. Classifier and helper stay only if tests show they help |
| [ADR-015](ADR-015.md) | No fine-tuning in v1 |
| [ADR-016](ADR-016.md) | Repo lives in a free GitHub organization. The Hugging Face demo Space stays on the personal Hugging Face account |
| [ADR-017](ADR-017.md) | Knowledge graph and GraphRAG added as Phase 9A. Engine chosen by test: LightRAG (MIT, actively maintained) or an own ontology-guided graph. Microsoft GraphRAG used only as a reference |
| [ADR-018](ADR-018.md) | Ontology written in LinkML (YAML) in configs/ontology/. It generates the Pydantic models and an OWL file |
| [ADR-019](ADR-019.md) | notebooks (workspaces on one topic) and study tools added as Phase 9B, all with citations. Audio and video overviews not added |
| [ADR-020](ADR-020.md) | Every step uses the verification loop (C12) and the verification number (C13) |
| [ADR-021](ADR-021.md) | The coding assistant writes the files after the owner approves each change (C3). A local rules file (kept out of Git) and docs/HANDOVER.md carry the rules and the progress between sessions |
| [ADR-022](ADR-022.md) | Project folder, repo and backup folder named multiagent-ai-lab. GitHub organization named mdu-ai-lab |

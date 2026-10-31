# Backup and recovery

| Field | Value |
|---|---|
| Purpose | How work is protected and restored |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Data privacy](../07-security/data-privacy.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

WORK_PLAN.md sections 6.3 and 6.4 are copied word for word below. They are the only backup rules.

Plan gap: the knowledge graph store (Phase 9A) and notebook data (Phase 9B) are not listed in section 6.3 or 6.4. Their storage and backup layer: REQUIRES CONFIRMATION.

## Storage layout on the SSD (WORK_PLAN.md section 6.3, word for word)

| Path | Content | In Git | Backed up to Drive |
|---|---|---|---|
| /Volumes/MacbookAPFS/Project/multiagent-ai-lab/ | The Git repo (code, configs, docs, tests, notebooks, exported results) | Yes | Through GitHub |
| .../multiagent-ai-lab/data/private/ | Private documents | No | No (rule V, see Q2) |
| .../multiagent-ai-lab/data/public/ | Public datasets | No | No (re-downloaded from pinned versions) |
| .../multiagent-ai-lab/data/annotations/ | Hand-made labels, golden insights, human judge checks | Yes (small text) | Yes |
| .../multiagent-ai-lab/mlflow/ | MLflow database and artifacts | No | Yes |
| Docker volume multiagent-ai-lab_qdrant_data (inside Docker Desktop's disk image on the SSD, see D30) | Search index | No | No (rebuilt from data) |
| .../multiagent-ai-lab/results/ | Exported result summaries for the dashboard | Yes | Through GitHub |
| /Volumes/MacbookAPFS/Project/multiagent-ai-lab-local/hf-cache/ | Downloaded model files (HF_HOME) | No | No (re-downloaded from pinned revisions) |
| .../multiagent-ai-lab-local/models/ | Embedding and reranker GGUF files converted locally (D32) | No | No (converted again, commands in docs/HANDOVER.md) |
| .../multiagent-ai-lab-local/tools/ | llama.cpp b11960, llama-swap v268, the llama.cpp converter source and its Python environment (D32) | No | No (downloaded again from pinned releases) |
| /Volumes/MacbookAPFS/Project/.uv-cache/ | uv cache (set by UV_CACHE_DIR in ~/.zshrc, see D27) | No | No |
| /Volumes/MacbookAPFS/Project/docker-data/ | Docker Desktop disk image (already on the SSD) | No | No |

Docker Desktop auto-start is off. Connect the SSD before starting Docker.

## Backup and working without the SSD (section 6.4, word for word)

Why not an exact full copy in Google Drive: the owner's Google Drive has 2 TB, so space is not the problem. The problem is safety: it is unsafe to run a Git repo, SQLite or Qdrant files inside a two-way synced folder: sync tools can corrupt them or create conflict copies.

The approach has 3 layers:

| Layer | What | Where | How it is restored |
|---|---|---|---|
| 1. Git | Code, configs, docs, notebooks, tests, small annotations, exported results, this plan | GitHub (public repo) | git clone |
| 2. Drive backup | MLflow folder, annotations, results not yet committed, handover files | Google Drive: multiagent-ai-lab-backup/backup/ (one-way copy with dated version folders) | rclone copy back to the SSD |
| 3. Re-creatable | Models, public datasets, venv, uv cache, Docker images, Qdrant index | Not backed up | make setup and make index from pinned versions |

Rules that prevent lost files and conflicts:

| # | Rule |
|---|---|
| 1 | GitHub is the only source of truth for code and docs. Google Drive never holds a working copy of the repo |
| 2 | One active machine at a time. Before switching: commit and push. On the other machine: pull first |
| 3 | Work done in Colab goes to a branch named remote/YYYY-MM-DD. Merge it on the Mac through a pull request so CI checks it |
| 4 | Result files are written once with unique names (run ID + date). They are never edited in two places |
| 5 | Drive backup is one-way (rclone copy with a dated backup folder). Nothing on Drive is deleted automatically. No two-way sync |
| 6 | Colab results go to Drive multiagent-ai-lab-backup/inbox/. On the Mac, make pull-inbox copies new files only (never overwrites) and imports them into MLflow |
| 7 | Check Drive usage monthly. The owner's Drive has 2 TB |
| 8 | Monthly restore test: restore the Drive backup into a temporary folder and check MLflow opens |
| 9 | Secrets (GitHub token, Hugging Face token) live in GitHub Secrets, Colab Secrets and your password manager. Never in Git or Drive |

What you can do when the SSD is unavailable: write and test code, run public-data experiments on Colab and update docs. Private-document work waits until the SSD is back.

Tools: Git (free), rclone (free, open source) on the Mac, the built-in Google Drive mount in Colab. Google Drive for Desktop is not needed.

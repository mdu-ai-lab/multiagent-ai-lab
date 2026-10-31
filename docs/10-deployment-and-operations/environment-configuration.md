# Environment configuration

| Field | Value |
|---|---|
| Purpose | Planned settings and profiles |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Secrets management](../07-security/secrets-management.md), [Deployment architecture](../04-architecture/deployment-architecture.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

Settings load through config.py from .env (0.1). Variable names are set in step 0.1 (.env.example and src/mrag/config.py). Environment variables override .env. Values marked as placeholders are confirmed in the step shown.

| Setting | Variable | Meaning | Value in .env.example | Source |
|---|---|---|---|---|
| Profile | MRAG_PROFILE | mac, gpu, demo, ci or company | mac | 0.1 |
| HF_HOME | HF_HOME | Model cache | /Volumes/MacbookAPFS/Project/.hf-cache | 0.1 |
| Data folder | MRAG_DATA_DIR | private/, public/, annotations/ and the SQLite file | data | 0.1 |
| Database URL | MRAG_DATABASE_URL | Empty means SQLite at data/app.db. PostgreSQL URL later | (empty) | 0.1, 15.3 |
| Model server address | MRAG_MODEL_SERVER_URL | llama-swap, vLLM or none (Transformers) | http://127.0.0.1:8080/v1 (placeholder) | 0.3, 0.5 |
| Qdrant address or in-process mode | MRAG_QDRANT_URL | Search store | http://127.0.0.1:6333 | 0.2, 5.2 |
| MLflow tracking address | MRAG_MLFLOW_TRACKING_URI | Experiments and traces. Port 5000 is used by macOS AirPlay Receiver | http://127.0.0.1:5001 (placeholder) | 1.2 |

Existing machine setup: uv cache on the SSD through UV_CACHE_DIR in ~/.zshrc (WORK_PLAN.md D27). Docker data on the SSD. Connect the SSD before starting Docker (WORK_PLAN.md section 6.3).

## Compute profiles (WORK_PLAN.md section 6.1, word for word)

| Profile | Hardware | Main model | Used for | Data allowed | Cost |
|---|---|---|---|---|---|
| Mac | MacBook Air M2, 16 GB, project on the 2 TB SSD | Qwen3.5-9B (vision, 4-bit GGUF) | Daily building, private documents, local API, UI, MLflow, Qdrant | Private and public | Free |
| GPU (main) | Google Colab free (T4, 16 GB, not guaranteed) | Qwen3.5-9B at higher precision through vLLM | Heavy evaluation, judge runs, parser and audio comparisons | Public only | Free, dynamic limits |
| GPU (backup) | Kaggle free (P100 or 2 x T4 = 32 GB) | Qwen3.8-27B if it runs well on 2 x T4 | Jobs needing 32 GB, load tests, backup when Colab has no GPU | Public only | Free, weekly quota |
| Demo | Hugging Face ZeroGPU Space | Qwen3.5-9B through Transformers (tested in 1.8) | Live public demo | Public sample documents only | Free, daily visitor quota |
| CI | GitHub Actions standard runner (CPU) | Qwen3.5-0.8B for smoke tests | Tests on every push | Public test fixtures only | Free (public repo) |
| Company server | Company Linux GPU server | Qwen3.8-27B or larger | Future company use | Company data inside their network | Paid by the company |

## Which environment for which task (section 6.2, word for word)

| Task | Environment | Why |
|---|---|---|
| Writing code, tests, API, UI | Mac | Full stack runs locally |
| Anything with private documents | Mac only | Privacy rule V |
| Small public experiments (dev sets, single route checks) | Mac | Fast enough, no upload needed |
| Building knowledge graphs for large public corpora | Colab free | Graph extraction calls the model for every chunk |
| Full test-set runs in the Mac profile | Mac (overnight, resumable jobs) | Measures what the group will really use |
| GPU-profile evaluation, judge runs, large public corpora | Colab free | GPU speed for public data |
| Parser and speech model comparisons on many pages or hours | Colab free | GPU speed |
| Anything needing more than 16 GB GPU memory (27B test, load test) | Kaggle free (2 x T4) | Only free option with 32 GB |
| Colab has no GPU available | Kaggle free | Backup |
| Live demo | ZeroGPU Space | Free GPU for visitors |
| SSD unavailable | Colab (code and public data only) or a temporary clone on the Mac's internal disk | See section 6.4 |

Rule of thumb: private data → Mac. Needs a GPU and the data is public → Colab. Needs more than 16 GB GPU memory → Kaggle.

# External integrations

| Field | Value |
|---|---|
| Purpose | Every outside service and its limits |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Integration architecture](../04-architecture/integration-architecture.md), [Secrets management](../07-security/secrets-management.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Service | Use | Data sent | Failure handling | Cost |
|---|---|---|---|---|
| Hugging Face Hub | Download models and datasets | None private | Pinned versions, cached on SSD | Free |
| Hugging Face ZeroGPU Space | Live demo | Public samples only | Health check 1.9 | Free, daily visitor quota |
| GitHub (organization) | Code, CI/CD, Pages, container images | Code and public results | CI gates | Free for public repos |
| Web search (smolagents WebSearchTool) | Opt-in online answers | Rewritten question only | Retry and message (8.1) | Free, rate-limited (to confirm in 8.1) |
| Google Drive (rclone) | Backup and Colab inbox | Non-Git project files, no private documents | Restore test | Owner's existing 2 TB plan, no new cost |
| Google Colab, Kaggle | Free GPU jobs | Public data only | Checkpoints, resumable jobs | Free, limits change |

Limits checked on 28 Oct 2026. Details: WORK_PLAN.md section 7.

## Free-tier register (WORK_PLAN.md section 7, word for word)

| Service | What is free | Limits | Can it charge you? | Guard |
|---|---|---|---|---|
| GitHub Actions | Standard runners in public repos | None for public repos on standard runners | Private repos past quota, larger runners (even in public repos) | Public repo, standard runners only |
| GitHub Pages | Public repos on GitHub Free and GitHub Free for organizations | Site max 1 GB, soft 100 GB bandwidth per month, soft 10 builds per hour (not for custom Actions workflows) | No. Over limits the site may stop being served | Small static site, custom Actions deploy. Dashboard address: mdu-ai-lab.github.io/multiagent-ai-lab |
| GitHub Container Registry | Public packages | Registry storage and bandwidth described as "currently free" | Private packages past quota | Public images only |
| Hugging Face ZeroGPU Space | Up to 2 Spaces for free accounts older than 30 days with a verified email | Gradio only. Daily GPU quota per visitor (free accounts 5 min). Sleeps when unused | Not without a payment method or credits | No payment method on HF. This project uses 1 of 2 Spaces |
| Hugging Face CPU or Docker Space | Not free for new Spaces | Paid plan required | Yes | Not used |
| Google Colab free | T4 GPU when available | Not guaranteed. Idle timeout and session cap | Only if you buy compute units | Never buy units |
| Kaggle notebooks | GPU (P100 or 2 x T4) | About 30 GPU hours per week (quota floats, not in official docs). 12-hour sessions | No | Public data only |
| Google Drive | The owner's existing 2 TB plan | Over quota blocks uploads and email | No new cost for this project | Monthly usage check |
| Docker Desktop | Personal use, education, small businesses, non-commercial open source | Paid for large organisations | Yes in large companies | Companies use Docker Engine on Linux (Phase 15 guide) |
| MLflow, Qdrant, llama.cpp, LangGraph, smolagents, Docling, Gradio, FastAPI, rclone, models | Open source or open weights, run locally | Mac RAM and disk | No | Licences checked when added |

Sources checked: docs.github.com (Pages limits, Packages billing), resources.github.com (2026 Actions pricing), huggingface.co/docs/hub (Spaces overview, ZeroGPU), support.google.com (Drive storage), docs.docker.com (Desktop licence). Colab and Kaggle limits come from secondary sources because neither publishes a fixed quota. Re-check these in step 1.7 and step 1.8 before relying on them.

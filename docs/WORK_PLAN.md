# Work Plan: Local Multi-Agent RAG Platform

Plan version 1.9, 31 October 2026. Owner: MDU (GitHub: Hossain007Bhuiyan).

This file is the single source of truth for the project. It is stored in the repo as docs/WORK_PLAN.md and is updated after every step.

## 1. Current state (update after every step)

| Item | Value |
|---|---|
| Plan status | Phase 0 in progress |
| Last completed step | Step 0.2 done. Details in docs/HANDOVER.md |
| Current phase | Phase 0. Next: step 0.3 |
| Repo | github.com/mdu-ai-lab/multiagent-ai-lab (public, owned by the GitHub organization mdu-ai-lab). Created 31 October 2026 |
| Live dashboard URL | Not created yet |
| Live demo URL | Not created yet |
| Latest version tag | None |
| Open issues | See section 4.2 (open questions) |

## 2. Project summary

| Item | Detail |
|---|---|
| Goal | A chat and document question-answering assistant that runs locally. Specialised agents and RAG work together so one platform can chat, answer questions over any supported file with page citations, search the web on request, summarise, extract JSON, calculate and plot from tables, and later transcribe audio |
| Users | The MDU university group first. Designed so companies that avoid cloud AI (for example Volvo) could run it inside their own network later |
| Why | The 4 MDU research works showed useful ideas but none released a usable public pipeline, API or frontend |
| Sources | Billah thesis (DVA504), Billah et al. journal article (Array), Chakravorty thesis (SAF-RAG), Wahab thesis (DVA429). Ideas are reused only where useful and cited as [Paper, Sec, page] |
| v1 scope | Chat, document Q&A, compare documents, web search (opt-in), summaries (long documents and reviews), extraction, calculations and plots, knowledge graph with ontology and GraphRAG, notebooks (workspaces on one topic) and study tools, audio (late phase), API, web UI, MCP, live dashboard, live demo |
| Non-goals in v1 | Fine-tuning, image generation, text-to-speech (including audio overviews (spoken summaries of sources), see Q10), video overviews, multi-machine scaling, SSO, paid hosting |
| Honesty rule | Never claim production-ready, real-time, automated or accurate unless implemented and verified. No system can promise zero hallucination. We reduce and measure it |

## 3. Requirements checklist (all instructions collected from the planning chat)

| # | Requirement | Where it is covered | Status |
|---|---|---|---|
| R1 | Advanced, professional chat prototype (not basic): multi-turn chat with memory, streaming answers, file upload and a chat list | Whole plan, phases 3 to 14 | Planned |
| R2 | Agents, RAG, LLMs and every needed model and tool | Sections 8 and 9, phases 3 to 14 | Planned |
| R3 | Any supported file type: PDF (digital and scanned), images, Word, PowerPoint, Excel, CSV, HTML, Markdown, text. Audio later | 3.2, 14.x | Planned |
| R4 | Questions over files with page citations and as little hallucination as possible | Phase 6 | Planned |
| R5 | Online information (web search) | Phase 8 | Planned |
| R6 | Summaries, reviews, extraction, calculations and plots, compare documents | Phases 7, 9, 10, 11 | Planned |
| R7 | Zero cost for development, hosting, deployment and API. No paid tiers. No trials treated as free | Sections 5 and 7, rule Z | Planned |
| R8 | Free open-weight Hugging Face models | Section 9 | Planned |
| R9 | Private documents never leave the Mac | Sections 5 and 6, steps 8.4, 12.x | Planned |
| R10 | Real public datasets. No synthetic data unless you agree | 2.1, 9.3 | Planned |
| R11 | Every technology has a real purpose | Section 9 (why column) | Planned |
| R12 | Project on the external 2 TB SSD | Section 6.3 | Planned |
| R13 | Backup in Google Drive, continue from Drive or Colab when the SSD is missing, sync back without conflicts | Section 6.4, step 0.6 | Planned |
| R14 | Use both MacBook Air M2 (16 GB) and Google Colab, chosen per task | Section 6.2 | Planned |
| R15 | Do not limit the design because of the MacBook. Use free cloud GPU when needed | Sections 6.1 and 6.2 | Planned |
| R16 | Push to GitHub after every step | Rule G | Planned |
| R17 | Live website that updates automatically after every push, before and after the API exists | Section 11, steps 1.7, 1.8 | Planned |
| R18 | API at the best stage, without rework | Step 1.6 (API-first), Phase 13 hardening | Planned |
| R19 | CI/CD and MLOps where they have a purpose | Phase 1 | Planned |
| R20 | MLflow for experiments, traces and versioning | 1.2, 1.3 | Planned |
| R21 | Testing, monitoring, documentation, version control, data management, security | 1.4, 1.9, 13.4, 16.2, section 6, Phase 12 | Planned |
| R22 | Future company use (on-prem, audit trail, versioned releases) | Phase 15 | Planned |
| R23 | A self-contained handover | Sections 1 and 15 | Planned |
| R24 | Easy English, step by step, why for each step | Rule C1 | Planned |
| R25 | Coding rules (flat modules, file creation by the coding assistant after approval, hashes, full commands, Git one per line, expected output, human style, no comma before and/or/but) | Section 5.2 | Planned |
| R26 | One phase at a time with checks and permission. Done/not-done table after each phase. What to do next after each step | Rule P | Planned |
| R27 | Copy-pasteable plan and a .docx copy | This file and WORK_PLAN.docx | Done (this file) |
| R28 | Repo owned by a GitHub organization from the start | Step 0.1, step 1.1 | Planned |
| R29 | GraphRAG: answers that follow relationships between entities across documents | Phase 9A | Planned |
| R30 | Ontology: a defined, versioned set of entity and relation types | Step 9A.1 | Planned |
| R31 | Knowledge base: collections, knowledge graph and saved notes together (interpretation, see Q11) | Phases 9A, 9B | Planned |
| R32 | Notebooks (workspaces on one topic): sources, chat, notes, study guide, FAQ, briefing, flashcards, quiz, mind map | Phase 9B | Planned |
| R33 | Verification loop: code, commands and expected output with a 12-character verification number per Python code file, checked locally with uv | Rules C12, C13, step 0.1 | Planned |

## 4. Decision log and open questions

### 4.1 Decisions

| ID | Decision | Reason | Replaced |
|---|---|---|---|
| D01 | Platform runs locally. Private documents stay on the Mac | Privacy for the group and future companies | — |
| D02 | Main local runtime: llama.cpp + llama-swap (GGUF, Metal) | One OpenAI-style server for chat, vision, embeddings, reranking and JSON output on 16 GB | Ollama (earliest plan) |
| D03 | Orchestration: LangGraph. Code agent and web tool: smolagents | Typed state, checkpoints, interrupts. smolagents for code-as-action | — |
| D04 | Search database: Qdrant (Docker on Mac, in-process mode in the demo) | Dense, sparse, multivector, filters and RRF in one engine | ChromaDB (earliest plan) |
| D05 | App database: SQLite through SQLAlchemy. Postgres by config in Phase 15 | Light on the Mac. Ready for servers | Postgres everywhere (earlier plan) |
| D06 | MLflow (local) for experiments, prompt and pipeline versions, traces and feedback | Versioning and audit trail. Free | SQLite trace table (short-lived plan) |
| D07 | CI on GitHub Actions (public repo, standard runners). CD for dashboard, demo and images | Free and needed because you push after every step | — |
| D08 | API-first: service.py + FastAPI skeleton in Phase 1. Hardening in Phase 13 | Avoids rework. UI, demo, tests and MCP share one contract | Whole API in Phase 13 |
| D09 | Live dashboard on GitHub Pages. Live demo on a free Hugging Face ZeroGPU Space (Gradio) | Both free. Pages never sleeps. ZeroGPU gives a free GPU for the demo | Streamlit (not needed). Free CPU Space (no longer free) |
| D10 | Cloud GPU: Google Colab free is the main cloud GPU. Kaggle free is the backup and the place for jobs needing 2 x T4 (32 GB) | You asked to use Colab. Colab free GPU is not guaranteed, so Kaggle covers gaps | Kaggle as main (last table). Colab premium (rejected: costs money) |
| D11 | GPU profile model: Qwen3.5-9B at higher precision on a Colab T4. Qwen3.8-27B tested on Kaggle 2 x T4 and used only if it runs well | A single free T4 (16 GB) is too small for the 27B model | 27B on paid Colab |
| D12 | Code and docs live in Git (GitHub = source of truth). Google Drive holds a one-way, versioned backup of non-Git files plus a Colab inbox. No two-way folder sync | File-sync tools can break .git folders and databases and create conflicts | — |
| D13 | Models, public datasets, venvs and indexes are not backed up. They are re-created from pinned versions | They can always be downloaded again, so a backup only costs time. The owner's Google Drive has 2 TB, so space is not the reason | — |
| D14 | Helper model Qwen3.5-2B, speech-to-text (late phase), MCP and an injection classifier are included. Classifier and helper stay only if tests show they help | Speed, audio files, interoperability, safety | — |
| D15 | No fine-tuning in v1 | Needs labelled or synthetic data. Few-shot beat small-data fine-tuning [Billah, Abstract, p. i] | — |
| D16 | Repo lives in a free GitHub organization. The Hugging Face demo Space stays on the personal Hugging Face account | Shared ownership for the group. Free ZeroGPU Spaces are for personal accounts; organizations need a paid plan | Repo under the personal GitHub account |
| D17 | Knowledge graph and GraphRAG added as Phase 9A. Engine chosen by test: LightRAG (MIT, actively maintained) or an own ontology-guided graph. Microsoft GraphRAG used only as a reference | Answers about relationships and whole-corpus themes. Microsoft GraphRAG is in maintenance mode and its indexing is expensive | — |
| D18 | Ontology written in LinkML (YAML) in configs/ontology/. It generates the Pydantic models and an OWL file | One source for entity and relation types, usable by extraction, the graph and other tools. Licence checked in 9A.1 | — |
| D19 | notebooks (workspaces on one topic) and study tools added as Phase 9B, all with citations. Audio and video overviews not added | Builds on summaries and the graph. Audio overviews need text-to-speech, which is a non-goal (Q10) | — |
| D20 | Every step uses the verification loop (C12) and the verification number (C13) | Fast, checkable steps: matching output and numbers show that the local file and result are exactly what the coding assistant checked. A working method the owner has used before | Rule C4 alone (hash check without a fixed method or loop) |
| D21 | The coding assistant writes the files after the owner approves each change (C3). A local rules file (kept out of Git) and docs/HANDOVER.md carry the rules and the progress between sessions | Faster, no copy-paste mistakes, the coding assistant reads the real files and git history. Each new session starts with the rules and the last session's report | Files created by the owner in VS Code (old C3). Handover only by attaching the plan |
| D22 | Project folder, repo and backup folder named multiagent-ai-lab. GitHub organization named mdu-ai-lab | Owner's decision | local-multiagent-rag, <organization-name> |
| D23 | Code licence Apache-2.0 (answers Q1) | Includes a patent grant, which suits later company use. Same licence as the main models | — |
| D24 | Group members get the Admin role on the multiagent-ai-lab repo. The owner stays the only organization Owner (answers Q8) | Full control of the repo without the power to delete the organization | Organization Owner for every member |
| D25 | Database migrations with Alembic from step 0.1. Its settings live in pyproject.toml ([tool.alembic]) and migrations/ | Every schema change is versioned from the first table. Helps the PostgreSQL switch in 15.3 | Migrations added later |
| D26 | The planning helper scripts stay in scripts/ in the project folder, ignored by Git | Owner's decision. They check the planning docs and are not part of the platform | — |
| D27 | uv cache on the SSD through UV_CACHE_DIR in the owner's ~/.zshrc (only when the SSD is connected) | Project/uv.toml is ignored inside a project whose pyproject.toml has a [tool.uv...] section, which this repo needs for the package name mrag | Project/uv.toml alone |
| D28 | Product comparisons removed from the repo and banned by rule C14. Each one replaced by a description of the real feature (for example "chat and document question-answering assistant", "notebooks (workspaces on one topic)") | Owner's decision: the words are vague and were only planning shorthand | "ChatGPT-style", "ChatGPT-like", "NotebookLM-style" |
| D29 | The coding assistant's rules file and settings stay out of Git through the local ignore file .git/info/exclude (not .gitignore). Repo files and commit messages name no assistant product (rule C15). The GitHub repo was deleted and created again on 31 October 2026 with one fresh commit, so the old history is gone | Owner's decision: the repo shows the project, not the tools used to build it | Rules file in the repo |
| D30 | Qdrant keeps its data in the Docker volume multiagent-ai-lab_qdrant_data inside Docker Desktop's disk image on the SSD | Tested 31 October 2026: with a folder shared from macOS, Qdrant v1.20.0 sees a FUSE file system and logs "Filesystem check failed ... may cause data corruption". The Docker volume (ext4) gives no warning. On Linux company servers both ways work | qdrant_storage/ folder in the repo |

### 4.2 Open questions (answer before or during the named phase)

| ID | Question | Needed by |
|---|---|---|
| Q1 | Code licence for the repo. Proposal: Apache-2.0. Confirm with the group | Answered 31 October 2026: Apache-2.0 (D23) |
| Q2 | Should private documents ever be backed up to Drive? Default: no. Option: encrypted with rclone crypt, only if you decide | Step 0.6 |
| Q3 | Is your Hugging Face account older than 30 days with a verified email? (needed for the free ZeroGPU Space) | Step 1.8 |
| Q4 | SPACE dataset licence (not yet verified). Replace if it blocks use | Step 2.1 |
| Q5 | SPACE key points: written by hand (default) or LLM-assisted (counts as synthetic, needs your approval) | Step 9.3 |
| Q6 | Swedish documents in v1 or later | Step 2.2 |
| Q8 | Which role "full access" means: Owner (controls the whole organization, including deleting it) or Admin (full control of the repo only) | Answered 31 October 2026: Admin on the repo (D24) |
| Q9 | Which domain ontology to build first (for example research papers or industrial documents) | Step 9A.1 |
| Q10 | Add audio overviews (spoken summaries of sources)? This needs a text-to-speech model and changes a non-goal | Before Phase 9B |
| Q11 | Does "Knowledge" mean the knowledge base described in R31 or something else? | Before Phase 9A |

## 5. Working rules

### 5.1 Project rules

| ID | Rule |
|---|---|
| Z | Zero cost. Public GitHub repo, standard runners only. No new payment method or paid plan for this project on GitHub, Hugging Face, Kaggle or Google. The owner's existing 2 TB Google Drive is used as it is. No paid tiers, no trials, no Colab compute units |
| P | One phase at a time. No code until "start Phase X". After each phase: check results, fix problems, show a done/not-done table, then ask before the next phase |
| S | End every step with what to do next |
| G | Commit and push after every step. Merge to main at phase end with a version tag. Update CHANGELOG.md and this file every step |
| L | Every push to main that passes CI rebuilds the dashboard and the demo automatically |
| A | Each feature phase adds its API endpoint and its demo feature together with the feature |
| V | Private documents never go to Colab, Kaggle, GitHub, Google Drive, the dashboard or the demo |
| E | Evaluations run in the Mac profile and, where useful, the GPU profile. Logged in MLflow and exported to the repo |
| H | Never guess. If unsure, say so and check. When something fails, find the real cause |
| T | Every technology must have a real purpose |
| N | Never claim production-ready, real-time, automated or accurate unless implemented and verified |
| K | Keep this project's chats separate from the thesis and presentation work. Do not teach the Hugging Face course |

### 5.2 Communication and coding rules

| ID | Rule |
|---|---|
| C1 | Very easy English, step by step, with why each step is needed |
| C2 | Flat modules in src/mrag/. Run with uv run python -m mrag.<module> |
| C3 | Code files are written by the coding assistant in the project folder, only after the owner approves each change. Never through terminal commands such as heredoc |
| C4 | Give a short hash check for every code file plus the Mac command to compute it |
| C5 | Write every command in full. Never say "the command from step X". Group independent commands |
| C6 | Git commands one per line (git add, git commit -m "...", git push), never chained with &&. Write the expected output under them. You only send output if it differs |
| C7 | Plain human code style with useful comments. No AI-looking formatting, no emojis, no long docstrings |
| C8 | Never put a comma directly before "and", "or" or "but" |
| C9 | Notebook instructions: label every cell with a descriptive name (plus Markdown or Code) |
| C10 | Steps use numbered sub-steps (for example 0.1.1, 0.1.2), each command block followed by a short Why |
| C11 | Do not create files (README, docs, images) unless asked. Planned docs in this plan count as asked when their step starts |
| C12 | Verification loop. For every step the coding assistant gives the code, the exact commands and the expected output, including the verification number of each Python code file. You run the commands with uv and compare. Everything matches: the step is done and you send nothing. Anything differs: you send only the different output. The coding assistant finds the real cause and gives the fix with new expected output. When an output can't be predicted exactly (for example real training results or live data), the coding assistant says so and you send that output before committing |
| C13 | Verification number: the first 12 characters of the SHA-256 of the file's Python syntax tree, `ast.dump(ast.parse(...))`. Comments and formatting do not change it. You run one inline command that lists the files: `uv run python -c "import ast, hashlib ..."` |
| C14 | No product comparisons such as "ChatGPT-style" or "NotebookLM-style" in any file in the repo (code, docs, README, commit messages). Describe what the feature does instead. The owner used such words in planning only to explain ideas |
| C15 | Repo files and commit messages never name the coding assistant product or its files. Its rules file and settings stay local (D29) |
| C16 | Code comments, config comments and commit messages never use the words "step" or "phase" and never use plan numbers. Describe the change itself. The docs keep the plan numbering |

## 6. Environments, storage and backup

### 6.1 Compute profiles

| Profile | Hardware | Main model | Used for | Data allowed | Cost |
|---|---|---|---|---|---|
| Mac | MacBook Air M2, 16 GB, project on the 2 TB SSD | Qwen3.5-9B (vision, 4-bit GGUF) | Daily building, private documents, local API, UI, MLflow, Qdrant | Private and public | Free |
| GPU (main) | Google Colab free (T4, 16 GB, not guaranteed) | Qwen3.5-9B at higher precision through vLLM | Heavy evaluation, judge runs, parser and audio comparisons | Public only | Free, dynamic limits |
| GPU (backup) | Kaggle free (P100 or 2 x T4 = 32 GB) | Qwen3.8-27B if it runs well on 2 x T4 | Jobs needing 32 GB, load tests, backup when Colab has no GPU | Public only | Free, weekly quota |
| Demo | Hugging Face ZeroGPU Space | Qwen3.5-9B through Transformers (tested in 1.8) | Live public demo | Public sample documents only | Free, daily visitor quota |
| CI | GitHub Actions standard runner (CPU) | Qwen3.5-0.8B for smoke tests | Tests on every push | Public test fixtures only | Free (public repo) |
| Company server | Company Linux GPU server | Qwen3.8-27B or larger | Future company use | Company data inside their network | Paid by the company |

### 6.2 Which environment for which task

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

### 6.3 Storage layout on the SSD

| Path | Content | In Git | Backed up to Drive |
|---|---|---|---|
| /Volumes/MacbookAPFS/Project/multiagent-ai-lab/ | The Git repo (code, configs, docs, tests, notebooks, exported results) | Yes | Through GitHub |
| .../multiagent-ai-lab/data/private/ | Private documents | No | No (rule V, see Q2) |
| .../multiagent-ai-lab/data/public/ | Public datasets | No | No (re-downloaded from pinned versions) |
| .../multiagent-ai-lab/data/annotations/ | Hand-made labels, golden insights, human judge checks | Yes (small text) | Yes |
| .../multiagent-ai-lab/mlflow/ | MLflow database and artifacts | No | Yes |
| Docker volume multiagent-ai-lab_qdrant_data (inside Docker Desktop's disk image on the SSD, see D30) | Search index | No | No (rebuilt from data) |
| .../multiagent-ai-lab/results/ | Exported result summaries for the dashboard | Yes | Through GitHub |
| /Volumes/MacbookAPFS/Project/.hf-cache/ | Model files (HF_HOME) | No | No (re-downloaded) |
| /Volumes/MacbookAPFS/Project/.uv-cache/ | uv cache (set by UV_CACHE_DIR in ~/.zshrc, see D27) | No | No |
| /Volumes/MacbookAPFS/Project/docker-data/ | Docker Desktop disk image (already on the SSD) | No | No |

Docker Desktop auto-start is off. Connect the SSD before starting Docker.

### 6.4 Backup and working without the SSD (safest practical approach)

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

## 7. Free-tier register (verified 28 October 2026)

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

## 8. Architecture and repo structure

### 8.1 Architecture

```
Browser (Gradio UI)  ·  Live demo (ZeroGPU Space)  ·  MCP clients
            │ HTTP /v1 (local)            │ in-process
            ▼                             ▼
        FastAPI (api.py) ───────► service.py (core functions)
                                          │
                     LangGraph supervisor (graph.py)
   Router → chat · document Q&A · compare · web · summary · extract · calc
                     │ Planner–Navigator–Reviewer (max 3, gated)
                     │ grounding.py (citations, claim check, refusal)
          ┌──────────┼───────────────┬──────────────────┐
     retrieve.py  rerank.py      llm_client.py       tools (web.py, calc.py sandbox)
          │                         │
       Qdrant              llama.cpp + llama-swap (Mac) · vLLM (Colab/Kaggle/company) · Transformers (demo)
          ▲
   worker.py: parse.py (Docling) → figures.py → chunking.py → pii.py → embed.py → index.py
   SQLite (users, collections, documents, versions, jobs, chat memory)
   MLflow (experiments, prompts, versions, traces, feedback) → export → results/ → dashboard
```

### 8.2 Repo structure (flat modules)

```
multiagent-ai-lab/
├── src/mrag/        config.py db.py llm_client.py service.py api.py auth.py ui.py
│                    jobs.py worker.py parse.py figures.py chunking.py pii.py versioning.py
│                    embed.py index.py retrieve.py rerank.py router.py graph.py qa.py planner.py
│                    ontology.py kg.py graphrag.py notebook.py study.py
│                    grounding.py memory.py web.py summary.py extract.py calc.py security.py
│                    audio.py tracing.py eval_data.py eval_metrics.py eval_run.py judge.py
│                    export_results.py site_build.py
├── demo/            app.py and requirements for the ZeroGPU Space
├── notebooks/       colab_gpu.ipynb kaggle_gpu.ipynb (every cell labelled)
├── configs/         settings, models.yaml, schemas/, ontology/, eval/
├── migrations/      Alembic database migrations (D25)
├── data/            private/ public/ annotations/ (only annotations in Git)
├── results/         exported result summaries (in Git)
├── tests/           unit/ integration/ e2e/ fixtures/
├── docs/            WORK_PLAN.md, HANDOVER.md, guides, data cards, system card
├── .github/workflows/  ci.yml pages.yml demo.yml health.yml release.yml
├── compose.yaml  Makefile  pyproject.toml  uv.lock  .env.example  LICENSE  README.md  CHANGELOG.md
```

## 9. Models, agents and tools register

| Type | Item | Purpose | Phase |
|---|---|---|---|
| Model | Qwen3.5-9B (Apache 2.0) | Main brain: chat, answers, vision, agents | 0 |
| Model | Qwen3.5-2B | Helper: routing and follow-up rewriting (kept only if tests support it) | 0, 7 |
| Model | Qwen3.5-0.8B | CI smoke tests on CPU | 1 |
| Model | Qwen3.8-27B (Apache 2.0) | GPU-profile tests on Kaggle and company servers | 1, 15 |
| Model | Qwen3-VL-Embedding-2B | Search vectors for text and page images (licence confirmed in 5.2) | 0, 5 |
| Model | Qwen3-VL-Reranker-2B | Reranking (licence confirmed in 5.4) | 0, 5 |
| Model | Gemma 4 12B and the largest Gemma 4 that fits the free GPU | Judge (different family from the generator) | 2 |
| Model | Docling layout and table models, OCR engine chosen by test, PaddleOCR-VL (compared) | Parsing and OCR | 3, 4 |
| Model | Presidio with its spaCy model | Personal data detection | 12 |
| Model | Small prompt-injection classifier (chosen by test) | Extra safety layer | 12 |
| Model | whisper.cpp or Granite Speech 5.0 (chosen by test) | Speech-to-text | 14 |
| Agent | Router, chat, document Q&A, compare, Planner–Navigator–Reviewer, web, summary, review analysis, Extractor–Verifier–Refiner, calculation, figure, claim checker | One per job | 4 to 11 |
| Tool | llama.cpp + llama-swap, vLLM, Transformers | Model serving per profile | 0, 1 |
| Tool | Qdrant | Hybrid search | 0, 5 |
| Tool | LangGraph, smolagents | Orchestration, code agent, web search | 7, 8, 11 |
| Tool | LightRAG or own graph (chosen in 9A.3), NetworkX | Knowledge graph and GraphRAG | 9A |
| Tool | LinkML | Ontology, generating Pydantic models and OWL | 9A |
| Tool | FastAPI, Gradio 6 (UI and MCP mode) | API, UI, MCP | 1, 13 |
| Tool | SQLite (Postgres later) through SQLAlchemy | App data, memory | 0, 15 |
| Tool | MLflow | Experiments, versions, traces, feedback | 1 |
| Tool | GitHub Actions, GitHub Pages, GHCR, Dependabot | CI/CD, dashboard, images, dependency updates | 1, 15 |
| Tool | Hugging Face ZeroGPU Space | Live demo | 1 |
| Tool | Colab free, Kaggle free | Free cloud GPU | 1 |
| Tool | rclone, Google Drive | Backup and Colab inbox | 0 |
| Tool | Docker (Qdrant, code sandbox), uv, pytest, ruff, mypy, pip-audit | Infra and quality | 0, 1 |

## 10. Implementation order and dependencies

### 10.1 Why this order

Foundations, delivery and measurement come first so every later feature is tested, versioned and visible from day one. Features then follow the data flow: files are parsed before they can be searched, searched before they can be answered, answered before agents can route them. Security, hardening and the company package come after all routes exist. Handover is last.

### 10.2 Phase dependencies

| Phase | Depends on | Reason |
|---|---|---|
| 0 Foundations | — | Base for everything |
| 1 MLOps, API and live delivery | 0 | Needs the repo, config and model client |
| 2 Evaluation base | 1 | Logs to MLflow, runs on Colab and Kaggle profiles |
| 3 Ingestion | 2 | Tested against the frozen test sets |
| 4 Charts and figures | 3 | Needs parsed figures and page images |
| 5 Retrieval | 3, 4 | Needs chunks and figure descriptions |
| 6 Grounded answers | 5 | Needs ranked evidence |
| 7 Agents and memory | 6 | Routes call the answer pipeline |
| 8 Web search | 7 | A route in the agent graph. Uses the claim check from 6 |
| 9 Summaries | 6, 7 | Uses section structure and the router |
| 9A Knowledge graph, ontology and GraphRAG | 3, 5, 6, 7 | Uses parsed chunks, search, grounding and the router |
| 9B Notebooks and study tools | 9, 9A | Uses summaries and the graph |
| 10 Extraction | 3, 7 | Uses parsed documents and the router |
| 11 Calculations | 3, 7 | Uses parsed tables and the router |
| 12 Security | 7 to 11, 9A, 9B | Protects all routes |
| 13 API hardening, UI, MCP | 1, 12 | Freezes the API built since Phase 1 |
| 14 Audio | 3, 5, 13 | New input type through the same pipeline and UI |
| 15 Company package | 13 | Packages the hardened system |
| 16 Handover | All | Final check |

## 11. Live website: how it works and updates

| Part | What it is | Before the full API (Phases 1 to 12) | After Phase 13 |
|---|---|---|---|
| Live dashboard | Static site on GitHub Pages: progress (done / not done per step), scores over versions, architecture, changelog, example cited answers on public documents | Built from results/ files that Mac, Colab or Kaggle runs exported and committed | Same, plus the final report |
| Live demo | Gradio app on a ZeroGPU Space with public sample documents | Calls service.py directly inside the Space. Gradio also exposes a free public API for the demo functions | Same UI as the full platform |
| Full API | FastAPI on the Mac (and later on company servers) | Grows every phase under /v1 (experimental) | Login, rate limits, frozen /v1, MCP |

Update flow on every push:

```
git push → CI on GitHub Actions (lint, types, tests, score check, security scan)
             │ only if green and on main
             ├─→ pages.yml: build site from results/ → GitHub Pages (live in minutes)
             └─→ demo.yml: upload demo/ and src/mrag/ → ZeroGPU Space (rebuilds itself)
weekly: health.yml checks both URLs and opens a GitHub issue if one is down
```

## 12. Phase plan

### Phase 0: Foundations on the Mac

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 0.1 Project setup | Create multiagent-ai-lab in /Volumes/MacbookAPFS/Project on the SSD. The existing Project/uv.toml keeps the uv cache on the SSD. Set up uv with Python 3.12 and the folders src/mrag, configs, data, results, tests, notebooks, demo and docs. Add a .gitignore so private data, public datasets, models, MLflow and Qdrant files never go to GitHub. Add .env.example for paths, ports and HF_HOME (/Volumes/MacbookAPFS/Project/.hf-cache). Write config.py to load all settings, including the profile (Mac, GPU, demo, CI or company server). Set up the database layer with SQLAlchemy (SQLite now). Add LICENSE (after Q1), a short README and CHANGELOG.md. Add a local rules file for the coding assistant, kept out of Git (D29): the working rules in short form (under 200 lines) and the instruction to read docs/WORK_PLAN.md and docs/HANDOVER.md before any work. Create the free GitHub organization mdu-ai-lab. Create the public GitHub repo inside the organization and push the first commit. | A clean, repeatable base. The profile switch lets the same code run everywhere. | uv run python -m mrag.config prints the settings. The repo is on GitHub with no data files. The coding assistant has loaded its local rules file. The uv check command (rule C13) prints the same numbers as the coding assistant for every Python file of this step. | Done |
| 0.2 Search database | Write compose.yaml with Qdrant, a fixed version and its data folder on the SSD. Start Docker only after the SSD is connected. | Qdrant stores all search data and must survive restarts. | Health check returns OK. Data is still there after a restart. | Done |
| 0.3 Mac model server | Install llama.cpp with Metal support and llama-swap. Download from Hugging Face, with fixed versions, to the SSD: Qwen3.5-9B (main), Qwen3.5-2B (helper), Qwen3-VL-Embedding-2B and Qwen3-VL-Reranker-2B. Write the llama-swap config: how each model starts and when it unloads after idle time. | One local address serves all models. Only models in use take RAM. | 5 test calls succeed: text chat, chat with an image, embedding, reranking and JSON output. | Not done |
| 0.4 Measure the Mac | A script loads the models alone and together. It records peak RAM, words per second and time to first word, and saves them to results/p0_resources.csv. Then we choose context size and quantisation. | 16 GB RAM is the Mac limit. We decide with numbers. | Peak RAM < 13 GB with main + embedding + reranker loaded. Settings saved in config. | Not done |
| 0.5 Model client | Write llm_client.py, one wrapper for all model calls. It supports an OpenAI-style server (llama.cpp on the Mac, vLLM on GPU) and a Transformers backend for the demo. The profile decides which one is used. | Moving between Mac, Colab, Kaggle, demo and company server needs no code change. | The same test call works through the wrapper with the Mac profile. | Not done |
| 0.6 Backup and sync | Install rclone and connect it to Google Drive. Create multiagent-ai-lab-backup with backup/ and inbox/ folders. Add make backup (one-way copy with a dated version folder, nothing deleted), make pull-inbox (copies only new files from inbox to the SSD) and make restore-test. Write the rules of section 6.4 into docs. Decide Q2. | Protects work that is not in Git. Allows work to continue from Colab without conflicts. | Backup runs. A file restored into a temp folder matches the original. Drive usage recorded. | Not done |
| 0.7 Plan in the repo | Put this file into docs/WORK_PLAN.md. Update its Current State and step status at the end of every step. | Every new chat and every group member reads the same, current plan. | docs/WORK_PLAN.md is on GitHub and shows Phase 0 progress. | Not done |

### Phase 1: MLOps, API and live delivery base

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 1.1 GitHub workflow | Protect the main branch. Use one branch per phase (plus remote/YYYY-MM-DD branches for Colab work). Commit and push after every step. Merge to main with a pull request at phase end and tag it (v0.1.0, v0.2.0 and so on). Keep CHANGELOG.md updated every step. Members work through pull requests on branches. Branch protection on main applies to everyone. | The group can follow every change. Any version can be restored. | First pull request merged with tag v0.0.1. | Not done |
| 1.2 MLflow | Add an MLflow server to compose.yaml, running locally with its data on the SSD. Create one experiment per route. Every run logs the git commit, config, model versions, dataset versions, metrics and result files. Turn on automatic tracing for LangGraph steps and model calls. export_results.py writes result summaries as JSON into results/ for the dashboard. | One place for all experiments and agent traces, at no cost. | A test run shows all fields. A trace shows each model call with time and tokens. The export creates JSON files. | Not done |
| 1.3 Versioning rules | Prompts go in the MLflow prompt registry. Each full pipeline setup is logged as a version. Datasets are pinned by Hugging Face revision and file hash. Models are pinned in models.yaml with their revision. Docker images are tagged with the release version. | Any result can be traced to the exact code, prompt, model and data. Companies need this audit trail. | Pick one old result and trace it to its exact versions. | Not done |
| 1.4 CI pipeline | GitHub Actions on every push and pull request, using standard runners only: ruff (style), mypy (types), pytest unit tests, an integration test with a tiny model (Qwen3.5-0.8B on CPU), pip-audit (package security), a secret scan and an evaluation gate that fails if committed scores drop below their limits. Dependabot proposes security updates. Artifacts kept small with short retention. | Every update is checked automatically, at no cost. | CI is green. A deliberately broken commit fails CI. | Not done |
| 1.5 Free GPU profile | Notebook templates for Colab free (main) and Kaggle free (backup), every cell labelled: clone the repo at a given commit, install with uv, start vLLM with the GPU profile model, run a job, save results with unique run IDs to Drive inbox (Colab) or the notebook output (Kaggle). Tokens come from Colab Secrets or Kaggle Secrets. make pull-inbox imports results into the Mac's MLflow. Jobs save checkpoints so a disconnect loses no work. Test Qwen3.5-9B on a Colab T4 and Qwen3.8-27B on Kaggle 2 x T4. Public data only. | Heavy work gets real GPU power for free, without touching private data. | The smoke test runs on Colab and on Kaggle. The chosen GPU models are recorded. The runs appear in the Mac's MLflow. | Not done |
| 1.6 API-first skeleton | service.py holds the core functions. api.py (FastAPI) wraps them under /v1 with health, version, models and chat endpoints, marked experimental. API docs are generated automatically. CI tests the endpoints. | Every later feature plugs into one contract. The UI, demo, tests and MCP use the same functions. | The API runs locally. All endpoint tests pass in CI. | Not done |
| 1.7 Live dashboard (CD) | site_build.py builds a static website from the repo and results/: progress table (done / not done per step from this file), latest scores per route with trend over versions, architecture diagram, changelog and example answers on public documents. pages.yml publishes it to GitHub Pages after CI passes on main. Re-check GitHub limits first. | Anyone in the group sees live progress for free. | The site URL works. A pushed change appears on it within minutes. Site size stays far below 1 GB. | Not done |
| 1.8 Live demo (CD) | After Q3 is confirmed, create a Gradio Space on ZeroGPU with public sample documents. It starts as a simple chat with the main model through Transformers and calls service.py directly. demo.yml uploads demo/ and src/mrag/ to the Space after CI passes on main. A note tells visitors about the daily GPU quota. Re-check Hugging Face limits first. | A working live demo during the whole project, at no cost. | The Space URL works. A pushed change appears after the Space rebuilds. | Not done |
| 1.9 Health checks | health.yml runs weekly on GitHub Actions. It checks that the dashboard and demo URLs respond and that links work. A failure opens a GitHub issue. | You learn about a broken live site without checking by hand. | A deliberately wrong URL creates an issue. | Not done |

### Phase 2: Evaluation base

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 2.1 Datasets | eval_data.py downloads LongDocURL, QASPER, TAT-DQA, CORD, GovReport, SPACE, 2WikiMultihopQA, MuSiQue and a public speech set, each with a fixed version. I read each licence and write a short data card: source, licence, size and use. If a licence blocks use (Q4), I propose a replacement and ask you. | Legal use. Anyone can repeat the results. | All datasets on the SSD. Every data card complete. | Not done |
| 2.2 Test sets | For each route, build a JSONL test set: question, correct answer, correct evidence (page or paragraph) and route label. Split by document so one document is never in both dev and test (20% dev, fixed seed). Decide Q6. | Dev is for tuning. Test is only for final scores, so scores stay honest. | A manifest lists counts and file hashes. | Not done |
| 2.3 Evaluation script | eval_metrics.py holds all metrics. Retrieval: Hit@5/10, MRR, nDCG@10. Answers: F1, exact match. Grounding: citation precision, FSCR, unsupported-claim rate. Summaries: coverage. Extraction: JSON validity, field accuracy with Wilson CI. Calculations: numeric match. Refusal: precision, recall, F1. Plus speed and RAM. eval_run.py runs a route on a test set and logs everything to MLflow. | Every later phase is judged by the same script. | Running the same test twice gives identical numbers. | Not done |
| 2.4 Baselines | Run the main model with no documents on every test set: Qwen3.5-9B on the Mac and the GPU profile models on Colab and Kaggle. | Shows how much the platform adds in each profile. | Baseline tables saved in MLflow and shown on the dashboard. | Not done |
| 2.5 Judge | judge.py uses a fixed scoring guide (correctness and faithfulness, 0–10). The judge is from another family than the generator: the largest Gemma 4 model that fits the free GPU for main results, and Gemma 4 12B for quick Mac checks. You hand-check 20 judged answers using a sheet I prepare. | A judge can be biased. We measure how far we can trust it. | Agreement number reported. Scoring guide frozen and versioned. | Not done |

### Phase 3: Ingestion

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 3.1 Upload and background jobs | jobs.py and worker.py. An upload saves the file and creates a job (queued). The worker takes jobs one by one and updates the status: parsing, indexing, done or failed with the reason. A crashed job starts again. | Big files take minutes. The chat must never freeze. | Kill the worker mid-job. After restart the job finishes. | Not done |
| 3.2 Parse every file type | parse.py uses Docling to turn PDF, Word, PowerPoint, Excel, CSV, HTML, Markdown, text and images into one common format: text blocks, headings, tables, figures, lists and page numbers. Unsupported types get a clear message. | Every later step reads one format only. | A sample file of each type parses correctly. | Not done |
| 3.3 OCR test | Run scanned pages (CORD receipts and scanned test pages) through each OCR option, including a document vision model. Measure character error rate and time per page. | OCR mistakes flow into every answer. Tool choice changes results [Journal, Sec 4.1, p. 9]. | Best engine chosen by numbers and set in config. | Not done |
| 3.4 Rich records | Save each part with file ID, version, page, heading path (for example "3 Methods > 3.2 Data"), position box, type and text. Render page images at a fixed resolution. | Needed for page citations, highlights and structure-aware search [Chakravorty, Sec 7.3.1, p. 22]. | Heading path on ≥ 95% of text parts. Every part has a page and a box. | Not done |
| 3.5 Versions and duplicates | versioning.py makes a sha256 fingerprint of each file. Same fingerprint: skip. Same name with a new fingerprint: new version, and old chunks are hidden from search but kept. Delete removes everything from that file. | No duplicates. Search always uses the latest version. | Tests for duplicate, new version and delete pass. | Not done |

### Phase 4: Charts and figures

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 4.1 Describe visuals | figures.py sends each chart, figure and table image to the vision model (Qwen3.5-9B on the Mac, the GPU profile model on Colab or Kaggle). The model writes title, axes, values and trend (tables as Markdown). The description is saved as its own part, linked to its page and box and marked "model-generated". | Search can't read pixels. This improved results in almost every test in Chakravorty's thesis [Chakravorty, Sec 8.6, p. 45]. | Every figure has a description linked to its page. | Not done |
| 4.2 Parser comparison | Pick 20 hard pages: complex tables, two columns, scans and charts. Compare Docling standard, Docling's vision pipeline and PaddleOCR-VL on text accuracy, table structure, time and RAM. | Choose the parser by evidence. | Results table done. Winner set in config. | Not done |
| 4.3 Prove it helps | Run figure and table questions from LongDocURL dev with and without the descriptions, in both profiles. | Confirms the gain with our own models. | Evidence found ≥ 5 points more often. Otherwise we rethink. | Not done |

### Phase 5: Retrieval

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 5.1 Chunking | chunking.py splits by section, with the size chosen by test (starting near 500 tokens). Each chunk starts with its heading path. Tables and figure descriptions stay as single chunks. Each chunk knows its parent section and neighbours. | Chunks keep meaning and context [Chakravorty, Sec 7.4.3, p. 24]. | No table is split. Every chunk has a heading path and a page. | Not done |
| 5.2 Indexing | embed.py and index.py create meaning vectors for chunks and page images, BM25 word vectors and a keyword index for codes and IDs. All go into Qdrant with collection, file, version, page, type and heading. Vectors are cached by chunk fingerprint. The same code also works with Qdrant's in-process mode, which Colab and the demo use. On GPU we also test a larger embedding model if one is published. Embedding licence confirmed. | Different search types catch different questions. The cache avoids repeated work. | All test files indexed. Re-indexing unchanged files creates 0 new vectors. | Not done |
| 5.3 Hybrid search | retrieve.py runs meaning, BM25, keyword and page-image search (20 results each) and merges them with RRF. The code always adds filters: the user's allowed collections, latest version and chosen files. | Hybrid search is the current standard. Filters enforce access control. | The filter test returns only allowed chunks. | Not done |
| 5.4 Reranking | rerank.py re-scores the top results with Qwen3-VL-Reranker, then adds a small structure score: heading match, same section, neighbours [Chakravorty, App. A, p. 57]. Keep the best 6–8. Add neighbours if space allows. Reranker licence confirmed. | Structural reranking gave the biggest gain in Chakravorty's thesis. | Better than no reranking on dev. | Not done |
| 5.5 Ablation tests | Add one part at a time on dev: dense only → + BM25 → RRF vs interleaving → + reranker → + structure score → + page images. Neural sparse is tested as an option. Final scores on test. Every step is logged in MLflow. | Keep only what really helps. | Best setup beats dense-only on nDCG@10 with CI above 0. Search p50 ≤ 2 s on the Mac. | Not done |

### Phase 6: Grounded answers

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 6.1 Cited answers | qa.py gives the model numbered sources [S1], [S2] with file and page. Rules: answer only from the sources, cite every claim, say "not found" when missing. Fixed context size. Answers stream word by word. The prompt is stored in the MLflow prompt registry. | The base of trustworthy answers. | Every test answer carries citations. | Not done |
| 6.2 Small-file mode | If a whole file fits the context size, give it all to the model instead of searching. Compare both ways on the test sets. The GPU profile allows larger files. | Full-context strategies covered far more in Wahab's thesis [Wahab, Sec 8.3, p. 44]. | Size rule per profile chosen by test numbers. | Not done |
| 6.3 Citation and claim check | grounding.py. First, every [S#] must be a real source. Second, the answer is split into sentences and the model checks each one against its cited source. Unsupported sentences are removed or marked "unverified". | The strongest guard against made-up content. | 100% valid citations. Unsupported claims ≤ 10%. | Not done |
| 6.4 Refusal | If the best search score is below a threshold, or the reviewer says the evidence is not enough, the answer is "I could not find this in your files", with the closest sources shown. The threshold is tuned on QASPER dev. | Saying "not found" is better than guessing [Wahab, Ch. 7, p. 35]. | Refusal F1 ≥ 0.70 on test. | Not done |
| 6.5 Highlight data | Each citation carries its page number and box coordinates for the UI. | The user can check evidence in seconds. | Every citation maps to a box. | Not done |

### Phase 7: Agents and memory

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 7.1 Router | router.py decides in 3 stages. Rules first (for example "extract" with a file goes to extraction, web toggle on goes to web). Then the helper model sorts the rest into JSON: route, files, needs web. If confidence is low, the main model decides or the system asks you. | Each request reaches the right agent. The helper keeps it fast. | ≥ 90% correct. Helper kept only if within 2 points of the main model. | Not done |
| 7.2 Agent graph | graph.py builds the LangGraph graph with chat, document Q&A and compare nodes. Compare searches each document separately, then answers side by side. All nodes share state: messages, chosen files, sources and limits. | One supervisor controls everything. New routes plug in easily. | Each node answers its test questions. | Not done |
| 7.3 Hard-question loop | planner.py runs only for hard or multi-part questions. Planner lists what is missing → Navigator runs focused searches → Reviewer scores the evidence. Stop at ≥ 7/10 or after 3 rounds. | Finds missing evidence. Used only when needed, because it can lower faithfulness and double time [Chakravorty, Abstract, p. iii; Sec 8.7, p. 47]. | Judge score up. Faithfulness drop ≤ 2 points. Otherwise it stays off. | Not done |
| 7.4 Limits and fallbacks | Per request: max 8 tool calls, 3 rounds, 120 s and a token cap. Backup path: agent loop → single answer → refusal. Vision fails → text only. Calculation fails → show the table. Every fallback is logged in the trace. | The system never hangs or loops. | 0 runaway loops in 200 runs. Every fallback tested. | Not done |
| 7.5 Chat memory | memory.py stores each chat with the LangGraph checkpointer. The helper model rewrites follow-ups ("what about 2023?") into full questions. Long chats get a running summary. Each chat remembers its files. | Natural multi-turn conversation. | Follow-up questions in test chats answered correctly. | Not done |

### Phase 8: Web search

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 8.1 Opt-in search | web.py. The web toggle is off by default. Only the rewritten question goes to the search engine, never file text. Uses smolagents WebSearchTool for the top 5 results. We confirm it works without an API key or payment. Rate limits get a retry and a clear message. | Online information, free, while files stay private. | Toggle off → 0 web calls. No key or payment needed. | Not done |
| 8.2 Read pages | Fetch the top pages. Docling turns HTML into clean text and keeps URL, title and date. The text is searched only for that question and is not saved into your collections. | Answers come from real page text, not short snippets. | Clean text with source for the test pages. | Not done |
| 8.3 Web citations | Web answers use [W1] with the URL and the same claim check. Mixed file + web answers keep the 2 source types apart. | Same trust level as file answers. | Every web citation points to a fetched URL. | Not done |
| 8.4 Leak test | During tests with private files open, log every outgoing request and scan it for file text. | Proves the privacy rule holds. | 0 matches. | Not done |

### Phase 9: Summaries

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 9.1 Long documents | summary.py summarises each section with citations, then combines them into one final summary. Length options: short, medium or detailed. Section summaries are made once at upload and reused. | Covers the whole document, unlike top-k search [Wahab, Sec 8.3, p. 44]. | Every main section appears in the summary. | Not done |
| 9.2 Reviews | pandas computes the statistics: count, average rating, rating spread, trend over time and common topics. Reviews are sampled across all ratings. The model writes the summary from the statistics block plus samples and cites review IDs. Numbers are copied from pandas, never invented. | Wahab's statistics strategy had top accuracy. LLMs count badly. | 100% of numbers match pandas. | Not done |
| 9.3 Test | Compare against a top-k RAG summary on GovReport and SPACE: coverage, FSCR, citation precision and time, in both profiles. Key points for SPACE are written by hand on a small set, unless you approve another method (Q5). | Proves the summary route is better. | Higher coverage (non-overlapping CI). FSCR ≥ 0.80. | Not done |

### Phase 9A: Knowledge graph, ontology and GraphRAG

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 9A.1 Ontology | ontology.py and configs/ontology/. Write the entity and relation types in LinkML (YAML): a general base (person, organization, place, date, concept, document section) plus the first domain ontology (Q9). Generate the Pydantic models and an OWL file from it. Version it in Git. LinkML licence checked. | One fixed, shared definition of what the graph may contain. The OWL file lets other tools read it. | Pydantic models and OWL file generate without errors. Changing the YAML and regenerating updates both. | Not done |
| 9A.2 Graph extraction | kg.py. A background job (per collection, optional) asks the main model to extract entities and relations from each chunk. Output is forced into the ontology's JSON schema. Every entity and relation keeps its source chunk, file and page. Same entities are merged by name and alias. Public corpora are built on Colab. | The graph is built from your files and every graph fact can be traced back to a page. | Every graph fact has a source page. Extraction precision measured on a hand-checked sample of 50 facts. Time and model calls recorded. | Not done |
| 9A.3 Engine choice | Compare LightRAG (MIT, actively maintained, uses our model server and embeddings) against our own ontology-guided graph (NetworkX with community detection). Graph data stays on the SSD. | Choose by evidence, not by name. | Comparison table on 2WikiMultihopQA dev. Winner set in config. | Not done |
| 9A.4 Graph route | graphrag.py. A new route in the router. Local questions use an entity's neighbourhood. Whole-corpus questions use community summaries. Answers cite the source pages behind each graph fact and go through the same claim check and refusal. The same collection filter as retrieve.py applies. | Questions about relationships and themes across many documents. | Router sends graph questions to this route. Every answer cites pages. Filter test passes. | Not done |
| 9A.5 Test | Compare hybrid RAG (Phases 5 and 6), GraphRAG and both together on 2WikiMultihopQA and MuSiQue: answer accuracy, citation precision, unsupported claims, time and model calls per document. | Proves when the graph helps and what it costs. | Results table logged in MLflow. Graph route kept only where it beats hybrid RAG. | Not done |

### Phase 9B: Notebooks and study tools

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 9B.1 Notebooks | notebook.py. A notebook is a named workspace: chosen sources, its chats and saved notes. Any answer can be saved as a note with its citations. Notebooks use the existing collection access rules. | Lets the group work on one topic over weeks with sources, chats and notes kept together. | Create a notebook, add sources, chat, save a note, reopen it with everything kept. | Not done |
| 9B.2 Study outputs | study.py. From a notebook's sources: briefing document, study guide with glossary, FAQ, timeline, flashcards and quiz. Built on the summary route (Phase 9) and the graph (9A). Every item cites its source. | Turns documents into learning and briefing material. | All 6 output types generate. 100% valid citations. Quiz answers checked against their sources. | Not done |
| 9B.3 Mind map | Build a mind map from the section structure and the knowledge graph. Saved as data for the UI (13.2). A simple view goes into the demo. | Shows how topics connect. | Mind map generates for a test notebook. Every node links to a source page. | Not done |
| 9B.4 Test | Run claim check and citation check on all study outputs for 5 public documents. You hand-check 20 flashcards and quiz questions. | Learning material must not contain made-up facts. | Unsupported claims ≤ 10%. Hand-check result recorded. | Not done |

### Phase 10: Extraction

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 10.1 Schemas | Each schema is a Pydantic model in configs/schemas, versioned in Git. We start with a CORD receipt (items, prices, totals). The group can add their own later. | A fixed contract for the output. | The CORD schema accepts CORD's correct answers. | Not done |
| 10.2 Extractor | extract.py sends the text (plus the page image if scanned) with the schema. The model server forces the output to match the schema. 2–3 examples from CORD dev are included. | Few-shot beat small-data fine-tuning [Billah, Abstract, p. i]. JSON templates worked in the journal [Journal, Sec 5.2, p. 21]. | 100% valid JSON. | Not done |
| 10.3 Verifier and Refiner | The Verifier checks types, required fields, that totals add up and that values appear in the source. The Refiner gets the error list and retries (max 2). Still failing → the UI asks you to review. | Self-correction loop [Journal, Sec 3.3, p. 7; Sec 4.2, p. 11]. | Field accuracy ≥ few-shot baseline, with Wilson CI. | Not done |
| 10.4 Export and batch | Export to JSON, CSV or Excel. Extract from many files in one batch job. | Practical use for the group. | Files open correctly. A batch of 100 completes. | Not done |

### Phase 11: Calculations

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 11.1 Find tables | calc.py finds the tables relevant to the question and loads them into pandas, cleaning numbers, percentages and currency. | Calculations need clean data. | Test tables load with correct types. | Not done |
| 11.2 Sandbox code | The smolagents CodeAgent writes pandas code. It runs in a Docker container with no network, read-only data, limited CPU and RAM, a 30 s timeout and only allowed libraries. | Code gives exact math. The sandbox keeps the machine safe. | Escape tests blocked: network, file writing, endless loop and huge memory. | Not done |
| 11.3 Plots | matplotlib saves a PNG that appears in the chat, with the code and the source table cited. | Answers like "plot revenue by year". | Plot appears for plot questions. | Not done |
| 11.4 Math test | Compare against the model answering alone on TAT-DQA math questions. | Proves the code agent helps. | ≥ 10 points better. | Not done |

### Phase 12: Security

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 12.1 Rule defences | security.py. File and web text are wrapped as data, and the model is told never to follow instructions inside them. Each route has an allowed-tools list. Document text can never trigger a tool. The UI shows text safely, with no HTML or scripts. | Documents and web pages can hide attack instructions. | Rule test suite passes. | Not done |
| 12.2 Injection classifier | Pick a small open classifier on Hugging Face (licence checked). Scan chunks at upload and web pages at fetch. Flagged parts are marked or excluded. Test on a public injection set and normal documents. | An extra layer on top of the rules. | Kept only if attack success drops and false alarms ≤ 2%. | Not done |
| 12.3 Personal data | pii.py uses Presidio to find names, emails, phone numbers and ID numbers. They are masked in traces, logs, MLflow and exports. Users with access still see the original answers. | Logs must not leak personal data. | 0 personal data in sampled traces. | Not done |
| 12.4 Access and limits | Users and collections in the database. Each user sees only their collections, enforced by the filter in retrieve.py. Limits: 50 MB per file, 1,000 pages, file type checked by content, question length and requests per minute. | Members' files stay separate. Abuse is blocked. | 0 leaks in a cross-user test. All limits tested. | Not done |

### Phase 13: API hardening, UI and MCP

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 13.1 API hardening | The API built since Phase 1 gets login (auth.py with tokens and hashed passwords), rate limits, clear error messages and a frozen /v1 contract (no longer experimental). | Safe for many users and for other apps to build on. | All API tests pass, including login and limit tests. | Not done |
| 13.2 Full web UI | ui.py with Gradio 6. Left: chat list. Centre: streaming chat, drag-drop files, web toggle. Right: sources with page preview and highlighted box. Also an extraction table view, export buttons, upload progress, a notebook view (9B) and a mind map and graph view (9A, 9B). The UI talks only to the API. The demo Space gets the same UI with public documents. | One chat interface for the group with chat list, streaming answers, files and sources. | A full chat works in the browser locally and in the demo. | Not done |
| 13.3 MCP | Offer search, ask and extract as MCP tools through Gradio's MCP mode, protected by login token. | Other AI tools can use the platform. | An MCP client calls the tools successfully. | Not done |
| 13.4 User feedback and monitoring | Thumbs up and down plus an optional comment on every answer, saved to its MLflow trace. A local monitoring view shows latency, errors, fallbacks and low-rated answers from the traces. | Shows where the system fails in real use. | Feedback appears on the right trace. The monitoring view shows the last 7 days. | Not done |
| 13.5 End-to-end test | pytest runs the full flow automatically, also inside CI. | Proves all parts work together. | Upload → ask → streamed cited answer with highlight. | Not done |

### Phase 14: Audio

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 14.1 Model comparison | audio.py tests whisper.cpp and Granite Speech 5.0 (licences checked) on the public speech set and 2 lecture-style recordings: word error rate, speed and RAM, on the Mac and on the free GPU. | Choose by evidence. | Best model per profile chosen. | Not done |
| 14.2 Audio pipeline | Audio becomes a timestamped transcript and then chunks, like text. Citations show the time range. The UI plays from that moment. The model loads only for audio jobs. | Questions about lectures and meetings. | A question about a recording cites the right time range. | Not done |

### Phase 15: Company deployment package

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 15.1 Docker images | Build Docker images for API, worker and UI. release.yml publishes them as public packages to GitHub Container Registry on each version tag. | A company installs exact, versioned images. Public packages are free. | Images build in CI and start correctly. | Not done |
| 15.2 GPU server profile | A compose file for a Linux GPU server: vLLM with the big models plus all platform services. The vLLM path is tested natively on Kaggle with public data, because notebooks can't run Docker. | Same platform on company hardware. | Compose file validated in CI. vLLM path works on Kaggle. | Not done |
| 15.3 Database switch | Switch from SQLite to PostgreSQL by config, including the LangGraph Postgres checkpointer. | Many users at once need a server database. | All tests pass on both databases. | Not done |
| 15.4 Load test | 10 users at the same time on the GPU profile (Kaggle) with public data. Measure speed and errors. | Shows what the system handles beyond one person. | Speed and error numbers reported. | Not done |
| 15.5 Deployment and security guide | How to run it inside a closed company network: no outgoing traffic except opt-in web search, audit log, backups, updates, access setup and a checklist for their security team. Licensing note: Docker Desktop needs a paid plan in large companies, so servers use Docker Engine on Linux. | Companies need this before any pilot. | Guide covers every service and setting. | Not done |

### Phase 16: Handover

| Step | What we will do | Why | Done-when test | Status |
|---|---|---|---|---|
| 16.1 One-command setup | Makefile: make setup installs everything and downloads models. make up starts all services. make down stops them. make eval runs all tests. make backup and make restore-test protect data. | The group starts it without knowing the details. | A fresh install works on the M2. | Not done |
| 16.2 Guides and cards | User guide: upload, ask, extract, read citations, limits. Developer guide: architecture, how to add a route, schema or model, how CI/CD, the dashboard, the demo, MLflow and backups work. System card: models used, intended use, limits, evaluation results. Data card summary. | The group can use and extend it after you, and knows its limits. | Every feature and every model covered. | Not done |
| 16.3 Final report | Results per route and profile against baselines, what helped and what didn't, known limits, RAM and speed. Also published on the live dashboard. | Honest proof of quality for the group. | Real numbers for every route. | Not done |
| 16.4 Group test | A group member installs it from the guide alone on their machine. We fix anything unclear. | The real handover test. | They succeed without your help. | Not done |

## 13. Datasets

| Dataset | Route | Licence (as checked so far) | Why |
|---|---|---|---|
| LongDocURL | Q&A, retrieval, visual | Apache 2.0 (Hugging Face card) | Long multimodal PDFs with evidence pages. Used by Chakravorty |
| QASPER | Q&A, refusal | CC BY 4.0 | Evidence paragraphs plus unanswerable questions |
| TAT-DQA | Tables, calculations | CC BY 4.0 | Real financial report pages with arithmetic |
| CORD | Extraction, OCR | CC BY 4.0 | Gold JSON per receipt (Indonesian receipts) |
| GovReport | Long-document summary | CC BY 4.0 (original release, confirm in 2.1) | Long reports with expert summaries |
| SPACE | Review summary | Not verified (Q4) | Many reviews per hotel with human summaries |
| MMLongBench-Doc (stretch) | Q&A visual | Apache 2.0 per a 2026 paper (confirm) | Second long-document check |
| 2WikiMultihopQA | GraphRAG | Apache 2.0 (per several 2025 and 2026 papers, confirm in 2.1) | Multi-hop questions grounded in entity relations |
| MuSiQue | GraphRAG | CC BY 4.0 per most sources. One paper says CC BY-SA 4.0. Confirm in 2.1 | Harder multi-hop questions |
| Public speech set | Audio | Chosen and checked in 2.1 | Word error rate test |
| Public injection set | Security | Chosen and checked in 12.2 | Attack tests |

## 14. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| A free tier changes (GitHub, Hugging Face, Colab, Kaggle, Google Drive) | Live site, demo or GPU access stops | The full platform always runs on the Mac. Re-check limits in 1.7 and 1.8. Health checks in 1.9 |
| Colab has no free GPU when needed | Delays | Kaggle backup. Jobs are resumable |
| 16 GB RAM pressure on the Mac | Slow or crashes | llama-swap unloading, one large model at a time, measured in 0.4 |
| Fanless M2 throttling during long jobs | Slow ingestion | Resumable jobs, overnight runs, Colab for public data |
| SSD unavailable or damaged | Lost local work | Git + Drive backup + restore test (6.4). Models and datasets re-created from pinned versions |
| Google Drive fills up (2 TB) | Backup and email stop | Monthly usage check |
| Sync conflicts between SSD, Drive and Colab | Lost or duplicated files | Git as source of truth, one-way backup, unique result names, remote branches (6.4) |
| 9B model weaker than large APIs | Lower accuracy | Strong retrieval, constrained output, claim check, refusal. Honest reporting |
| Agent loop hurts faithfulness or speed | Worse answers | Gated loop and ablation (7.3) |
| Local judge bias | Misleading scores | Other-family judge, human check, deterministic metrics first (2.5) |
| Dataset licence or fit | Can't use a dataset | Checked in 2.1, replaced if needed |
| Hidden instructions in documents or web pages | Data leak or misuse | Phase 12, sandbox, no tools from document text |
| Model or package supply chain | Tampered files | Pinned revisions and hashes, uv.lock, pip-audit, Dependabot |
| Fast-moving tools | Breaking upgrades | Pin everything. Upgrade only through the CI evaluation gate |
| Scope creep | Never finish | Non-goals list, phase gates |
| Graph extraction is slow on the Mac and costs many model calls | Long ingestion | Graph is optional per collection. Large public corpora on Colab. Time and calls measured in 9A.5 |
| The main model extracts wrong entities or relations | Wrong graph answers | Ontology-constrained JSON output, source citation for every graph fact, claim check, test in 9A.5 |
| GraphRAG does not beat hybrid RAG | Wasted effort | Kept only where tests show it helps (D17) |
| Docker Desktop licence in companies | Unexpected cost for a company | Docker Engine on Linux servers (15.5) |
| Context lost between chats | Wrong decisions repeated | This file, decision log, end-of-chat checklist |

## 15. Handover procedure

### 15.1 End-of-chat checklist (do this before leaving every chat)

1. Finish the current step completely or roll it back. Never leave a step half done.
2. Update this file: step status, Current State table (section 1), decision log (4.1), open questions (4.2).
2a. Update docs/HANDOVER.md: files changed, test results, problems and fixes, deviations from the plan and the exact next step.
3. Commit and push (git add, git commit -m "...", git push). Merge and tag if a phase ended.
4. Check that CI is green and the dashboard shows the new status.
5. Run make backup.
6. Download docs/WORK_PLAN.md from GitHub for the next chat.

# Handover

Report of the last work session. Read this after docs/WORK_PLAN.md at the start of every session.

## Session 31 October 2026: step 0.3

Step: 0.3 Mac model server. Status: done.

### What was done

- llama.cpp build b11960 (the code of release v0.8.0, 28 October 2026) and llama-swap v268 from
  their GitHub releases. The SHA-256 of both downloads matched the published values. Metal works:
  Apple M2 with about 12 GB usable GPU memory (MTL0 12124 MiB).
- Models (all Apache-2.0, pinned revisions, SHA-256 of every large file checked):

| Model | Source | Files |
|---|---|---|
| Qwen3.5-9B (main) | unsloth/Qwen3.5-9B-GGUF at 3885219b6810 | Qwen3.5-9B-Q4_K_M.gguf, mmproj-F16.gguf |
| Qwen3.5-2B (helper) | unsloth/Qwen3.5-2B-GGUF at f6d5376be1ed | Qwen3.5-2B-Q8_0.gguf (text only) |
| Qwen3-VL-Embedding-2B | Qwen/Qwen3-VL-Embedding-2B at 9f2f7e710d6d, converted locally | Qwen3-VL-Embedding-2B-Q8_0.gguf, mmproj-Qwen3-VL-Embedding-2B-F16.gguf |
| Qwen3-VL-Reranker-2B | Qwen/Qwen3-VL-Reranker-2B at 4bd860ac4f15, converted locally | Qwen3-VL-Reranker-2B-Q8_0.gguf, mmproj-Qwen3-VL-Reranker-2B-F16.gguf |

- configs/llama-swap.yaml: one llama-server per model, paths from environment variables,
  127.0.0.1 only, --offline, unload after 600 s without requests.
- .env.example: HF_HOME now points to multiagent-ai-lab-local/hf-cache. New MRAG_LLAMA_SERVER and
  MRAG_MODELS_DIR.
- File check: the SHA-256 of configs/llama-swap.yaml starts with a8dc4b57d2c8. No Python file
  changed, so the verification numbers are unchanged.

### How to repeat the conversion

The Python environment comes from requirements/requirements-convert_hf_to_gguf.txt of the same
build (torch 2.11.0, transformers 4.57.6, numpy 2.2.6). Commands for the reranker (the embedding
model is the same with its own snapshot folder and file names):

```
cd /Volumes/MacbookAPFS/Project/multiagent-ai-lab-local/tools/llama.cpp-src-b11960
HF_HUB_OFFLINE=1 ../llama-convert-venv/bin/python convert_hf_to_gguf.py /Volumes/MacbookAPFS/Project/multiagent-ai-lab-local/hf-cache/hub/models--Qwen--Qwen3-VL-Reranker-2B/snapshots/4bd860ac4f15ad1897a214615cccc700f8f71818 --outtype q8_0 --outfile /Volumes/MacbookAPFS/Project/multiagent-ai-lab-local/models/Qwen3-VL-Reranker-2B-Q8_0.gguf
HF_HUB_OFFLINE=1 ../llama-convert-venv/bin/python convert_hf_to_gguf.py /Volumes/MacbookAPFS/Project/multiagent-ai-lab-local/hf-cache/hub/models--Qwen--Qwen3-VL-Reranker-2B/snapshots/4bd860ac4f15ad1897a214615cccc700f8f71818 --mmproj --outtype f16 --outfile /Volumes/MacbookAPFS/Project/multiagent-ai-lab-local/models/mmproj-Qwen3-VL-Reranker-2B-F16.gguf
```

Embedding snapshot folder: models--Qwen--Qwen3-VL-Embedding-2B/snapshots/9f2f7e710d6d81056aa5c0a4f04764fec6bb7bda

### How to start the model server

In Terminal, in /Volumes/MacbookAPFS/Project/multiagent-ai-lab:

```
set -a
source .env
set +a
/Volumes/MacbookAPFS/Project/multiagent-ai-lab-local/tools/llama-swap-v268/llama-swap --config configs/llama-swap.yaml --listen 127.0.0.1:8080
```

### Test results (coding assistant, through llama-swap from configs/llama-swap.yaml)

| Test | Result |
|---|---|
| Text chat (Qwen3.5-9B) | "The capital of Sweden is Stockholm." About 14 tokens per second |
| Chat with an image (red and blue halves) | Described the red left half and the blue right half correctly |
| Embedding | 2048 dimensions. Similar sentences 0.888, unrelated 0.238 |
| Reranking | Correct document first (0.751), related wrong document 0.446, unrelated 0.249 |
| JSON output with a schema | {"city": "Stockholm", "country": "Sweden"} |
| Helper (Qwen3.5-2B) | Answers |

### Problems and fixes

- The community reranker GGUF (mradermacher) has no rank pooling and no cls.output tensor, so it
  cannot rerank. Fix (D32): converted locally. Its header now has pooling_type 4 (rank) and the
  classifier labels yes and no. The cls.output.weight tensor is present.
- GPU out of memory with the main, embedding and reranker models loaded together
  ("Insufficient Memory", kIOGPUCommandBufferCallbackErrorOutOfMemory) with context sizes
  8192, 4096 and 8192. The failed llama-server stays broken until it is restarted. Fix for now:
  only one model runs at a time (llama-swap default).
- VS Code copies .env into each terminal when the terminal opens. These values override .env. After changing .env, open a new terminal. The start command above loads .env itself.
- The folders .hf-cache, tools and models were first created directly in Project/ and then moved
  into Project/multiagent-ai-lab-local (owner's decision, D31). The converter environment was
  created again after the move. All tests passed again afterwards.

### Deviations from the plan

- One model at a time instead of all models together, until step 0.4 measures what fits.
- Downloads are in multiagent-ai-lab-local/hf-cache instead of Project/.hf-cache (D31).
- llama-server uses the rerank template written by the converter. It adds empty think tags that
  Qwen's own reranker template does not have, so scores can differ slightly from Qwen's
  reference. To be measured in steps 5.4 and 5.5.
- Qwen3.5-9B thinks before it answers by default. When to switch thinking off is decided in
  later phases.
- The step 0.1 point "HF_HOME from .env is not exported" is solved for the model server by the
  start command.

### Notes for later steps

- Step 0.4: context sizes and quantisation in configs/llama-swap.yaml are first values. The GPU
  limit is about 12 GB.
- The internal model name of the converted files is the revision hash (cosmetic only).
- ggml-org/Qwen3.5-0.8B-GGUF (published by the llama.cpp team) exists for the CI tests in step 1.4.

### Exact next step

Next session (connect the SSD first):
1. Step 0.4 Measure the Mac: a script loads the models alone and together, records peak RAM,
   words per second and time to first word in results/p0_resources.csv, then context size and
   quantisation are chosen. Ask the owner before writing any file (rule C3).

## Session 31 October 2026: step 0.2

Step: 0.2 Search database. Status: done.

### Start-of-session checks

- Mac and GitHub in sync, all files from the last handover present, uv sync and
  mrag.config work, verification numbers unchanged, the rules file is only in
  .git/info/exclude and no assistant names are on GitHub.
- Step 0.1 marked done (all its done-when checks passed).

### What was done

- compose.yaml: Qdrant v1.20.0 (latest stable release, 22 October 2026, arm64 image),
  REST port 6333 on 127.0.0.1 only, data in the Docker volume
  multiagent-ai-lab_qdrant_data, usage statistics off (QDRANT__TELEMETRY_DISABLED).
- File check: the SHA-256 of compose.yaml starts with 91e40b0d630d. No Python file
  changed, so the verification numbers are unchanged.

### Test results (owner and coding assistant)

| Test | Result |
|---|---|
| docker compose up -d | Network, volume and container created |
| Health check /healthz | healthz check passed |
| Qdrant log | No filesystem warning. "Telemetry reporting disabled". Version 1.20.0 |
| Storage file system inside the container | ext2/ext3 (ext4 family) |
| Collection restart_test after docker compose restart | Still there |
| Collection after docker compose down and up (container created again) | Still there |
| Test collection deleted | Collections list empty |

### Problems and fixes

- A folder shared from macOS shows up as FUSE inside the container. Qdrant v1.20.0 then
  logs "Filesystem check failed ... FUSE filesystems may cause data corruption due to
  caching issues" (tested with a temporary folder on the SSD, deleted afterwards).
  Fix (owner approved, D30): a Docker volume inside Docker Desktop's disk image, which
  is on the SSD (/Volumes/MacbookAPFS/Project/docker-data/DockerDesktop).

### Deviations from the plan

- Section 6.3 named qdrant_storage/ in the repo. Qdrant now uses the Docker volume (D30).
  qdrant_storage/ stays in .gitignore (unused, harmless).
- Only port 6333 is published. The gRPC port 6334 is added when a module needs it.

### Notes for later steps

- docker compose down -v, docker volume prune --all and a Docker Desktop reset delete the
  Qdrant data. It can be rebuilt from the documents.
- The volume name comes from the folder name multiagent-ai-lab.
- The Python Qdrant client added later must match server v1.20.0.
- Company guide (15.5): on Linux a volume or a folder on a dedicated disk both work.
  On Mac and Windows use a volume.

### Exact next step

Next session (connect the SSD first, then start Docker Desktop):
1. Step 0.3 Mac model server: llama.cpp with Metal, llama-swap and the 4 models
   downloaded to /Volumes/MacbookAPFS/Project/.hf-cache. HF_HOME must reach the
   download tools (see the step 0.1 deviations below). Ask the owner before writing
   any file (rule C3).

## Session 30 to 31 October 2026: step 0.1

Step: 0.1 Project setup. Status: done.
Sub-steps 0.1.1 and 0.1.2 written and tested by the coding assistant, then verified by the owner (output
and verification numbers matched). 0.1.3 organization and public repo created by the owner.
0.1.4 first commits pushed, then the repo was deleted and created again with one fresh commit
(decision D29). The earlier commits no longer exist on GitHub.
0.1.6 this update.

### Done-when test of step 0.1

| Check | Result |
|---|---|
| uv run python -m mrag.config prints the settings | Passed (owner) |
| Repo on GitHub with no data files | Passed. Checked by the coding assistant through the GitHub API after the repo was created again: 124 files, no .env, no database, nothing from data/private, data/public, scripts/ or .vscode/ |
| The coding assistant has loaded its local rules file | Passed. Checked at the start of the next session on 31 October 2026 |
| Verification numbers match (rule C13) | Passed (owner) |

### Owner decisions in this session

| Item | Decision |
|---|---|
| Q1 licence | Apache-2.0 |
| Q8 "full access" | Admin role on the multiagent-ai-lab repo. The owner stays the only organization Owner |
| Migration tool | Alembic from the start |
| scripts/ (planning helper scripts) | Stay in the project folder, ignored by Git |

### Files created

pyproject.toml, uv.lock, .python-version, .gitignore, .env.example, LICENSE (official
Apache-2.0 text from apache.org), README.md, CHANGELOG.md, a local rules file for the coding assistant (not in Git), docs/HANDOVER.md,
src/mrag/__init__.py, src/mrag/config.py, src/mrag/db.py, migrations/env.py,
migrations/script.py.mako and the planned empty folders (configs, data/annotations, results,
tests/unit, tests/integration, tests/e2e, tests/fixtures, notebooks, demo, migrations/versions).
data/private and data/public exist only locally.

### Test results (run by the coding assistant on the Mac)

| Test | Result |
|---|---|
| uv sync | Python 3.12.14, 12 packages: alembic 1.20.1, pydantic-settings 2.16.2, sqlalchemy 2.1.6 and their dependencies |
| uv run python -m mrag.config (without and with .env) | Prints all 7 settings |
| Environment variable overrides .env | Works (MRAG_PROFILE=ci) |
| Wrong profile value | Clear error listing the allowed values |
| uv run alembic upgrade head, alembic current | Work. SQLite file created at data/app.db |
| SQLite settings | foreign_keys = 1, journal_mode = wal |
| Alembic revision template | A generated revision parses. Test revision deleted afterwards |

Verification numbers (rule C13): src/mrag/__init__.py 3543b4693a36, src/mrag/config.py
4239cc4118f7, src/mrag/db.py 511eeaebbdbd, migrations/env.py c95357b4cf62.

### Problems and fixes

- uv cache not on the SSD inside this project. Cause: uv stops looking for config files at the
  first pyproject.toml that has a [tool.uv...] section. Ours has [tool.uv.build-backend]
  (needed for the package name mrag), so /Volumes/MacbookAPFS/Project/uv.toml is ignored and
  uv uses ~/.cache/uv on the internal disk. Fix (owner approved): ~/.zshrc now sets
  UV_CACHE_DIR=/Volumes/MacbookAPFS/Project/.uv-cache when the SSD is connected. Checked in a
  new shell: uv cache dir prints the SSD path. Nothing machine-specific is in the repo.

### Deviations from the plan

- New folder migrations/ (Alembic). Not in WORK_PLAN.md section 8.2 yet.
- No alembic.ini: Alembic settings are in pyproject.toml under [tool.alembic].
- SQLite file at data/app.db. Its backup layer is not in section 6.3 or 6.4 yet. To decide in step 0.6.
- MLflow default port 5001 instead of 5000 (macOS AirPlay Receiver uses 5000).
- Model server port 8080 in .env.example is a placeholder until step 0.3.
- HF_HOME from .env is read by config.py but not exported to the environment. Step 0.3 must make
  sure the model download tools use /Volumes/MacbookAPFS/Project/.hf-cache.
- docs/07-security/secrets-management.md says .env.example lists names without values.
  WORK_PLAN.md step 0.1 asks for paths, ports and HF_HOME in it, so it has safe default values
  and no secrets.

### Docs updated (WORK_PLAN.md v1.8)

- WORK_PLAN.md: Current State, decisions D23 to D27, Q1 and Q8 answered,
  uv cache row in 6.3, migrations/ in 8.2, step 0.1 status.
- All 99 other docs: status banner, link to WORK_PLAN.md v1.8 and Last updated date. Rows copied
  word for word from WORK_PLAN.md (Q1, Q8, uv cache, 8.2) updated to match.
- README.md, database-design.md, environment-configuration.md, testing-status.md, roadmap.md,
  milestones.md: status and decided items. ADR-005 title fixed (it said Phase 1, the decision says Phase 15).
- .gitignore also ignores .vscode/ (personal editor settings).

### Repo created again: no assistant names

- Owner's decision D29 and new rule C15: the coding assistant's rules file and settings stay
  local (.git/info/exclude, never pushed). Repo files and commit messages name no assistant
  product. Every such mention in README.md, CHANGELOG.md and docs/ now says "the coding assistant".
- The GitHub repo was deleted and created again with one fresh commit, so the old
  history is gone. Checked: the GitHub API no longer finds the old commits.
- Owner's rule C16: no "step", "phase" or plan numbers in code comments, config comments or commit
  messages. Comments in db.py, config.py and .env.example reworded (verification numbers unchanged,
  only comments changed). The message of the first commit was corrected the same way.
- Owner's feedback: fix only exactly what needs fixing. Never delete and re-push everything when
  a targeted fix is possible.

### Earlier: vague wording removed (WORK_PLAN.md v1.9)

- First commit pushed to github.com/mdu-ai-lab/multiagent-ai-lab (organization and public repo
  created by the owner).
- Owner's decision D28 and new rule C14: no product comparisons ("ChatGPT-style", "ChatGPT-like",
  "NotebookLM-style") in the repo. All 31 places in README.md and docs/ (13 files) now describe the
  real feature instead. The words remain only inside rule C14 and decision D28, which name them
  in order to ban them.
- The local rules file has rule C14. docs/11-development-standards/coding-standards.md has the C14 row
  (word-for-word copy of section 5.2). All doc links point to WORK_PLAN.md v1.9.
- Owner's decision: the README description is only "Work in Progress" for now. A description
  is written later, when features exist.

### Exact next step

Next session (connect the SSD first):
1. Step 0.2 (Qdrant in compose.yaml with a fixed version and its data folder on the SSD).
   Start Docker only after the SSD is connected. Ask the owner before writing any file (rule C3).

Not done yet by plan design (later steps): CI (1.4), make backup (0.6). The end-of-session
checklist items for CI and backup can't run until those steps exist.

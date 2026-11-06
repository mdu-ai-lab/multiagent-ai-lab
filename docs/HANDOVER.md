# Handover

Report of the last work session. Read this after docs/WORK_PLAN.md at the start of every session.

## Session 6 November 2026: MLflow (step 1.2)

- MLflow 3.17.2 (D40). The mlflow-skinny client is in the project environment. The full server
  has its own locked environment in ops/mlflow-server, because the two packages install the
  same files (1,326 shared files, counted in the 3.17.2 install files).
- make mlflow starts the server on 127.0.0.1:5001 with its data in mlflow/. It only accepts an
  address on this Mac and turns off usage statistics.
- tracing.py: one trace per request with its totals (tokens in and out, model calls, tool
  calls, time, fallback) and one span per model call. Runs record the git commit, config
  fingerprints, model and dataset versions, metrics and result files. Only runs marked for
  publishing are exported. On in the mac profile only. service.py calls tracing.setup() from
  step 1.6.
- llm_client.py records chat, streamed chat, embedding and rerank calls inside a request.
  Streamed answers report their token counts (stream_options include_usage, confirmed with
  llama.cpp b11960).
- export_results.py writes published runs to results/<route>/<date>_<run id>.json. Without a
  running server it stops at once with a message.
- make backup takes a clean copy of mlflow/mlflow.db. make restore-test checks its integrity
  and that MLflow opens it. Not run yet.
- Tests: 52 unit tests and 10 Mac tests with both servers passed. AT-1.2 passed. Commits
  6491fb1 to 1600e62.
- Checked on the Mac: run file links start with mlflow-artifacts:, so the mlflow folder can
  move to another computer. The server tells the MLflow page that usage data is off
  (disable_ui_telemetry true). The page still shows an information box about usage data.
  MLflow with its workers used about 125 MB (RSS).

Notes for later steps:
- MLflow 3.17.2 lists its automatic OpenAI tracing as tested only with openai 2.2.0 to 2.47.0.
  Model calls are therefore traced inside llm_client.py. Check MLflow's tested range for
  LangGraph before its tracing is turned on in 7.2.
- The tests show one warning from SQLAlchemy 2.1 about MLflow's database code (noload).
- Every run of the Mac tests adds one trace and one run to the MLflow experiment
  integration-test.
- One push failed with "fatal error in commit_refs_rules" on GitHub's side. The same push
  worked on the second try.
- Suggested: run make backup and make restore-test once, because the backup code changed in
  this step. Before that, create the own Google Drive client_id for rclone (note of 4 November).

### Exact next step

1. Step 1.3 (versioning rules), shown to the owner for approval first.

## Session 5 November 2026: GitHub workflow (step 1.1)

- gh 2.103.3 from Homebrew, logged in as Hossain007Bhuiyan.
- Repo settings: merge commits only. Branches are not deleted after a merge.
- Ruleset protect-main (id 26650257) on the default branch: pull request required with 0
  approvals, no deletion, no force push, merge method merge, no bypass. GitHub also set
  require_extra_approval_for_unattributed_changes to true by default. Its effect is not
  documented and not checked.
- Branch phase-1. Commit 46b3d12 records version 0.0.1 in CHANGELOG.md.
- AT-1.1 passed: a direct push of phase-1 to main was refused (GH013, "Changes must be made
  through a pull request"). Pull request #1 merged with merge commit 62c367c, tag v0.0.1.
- No code changed. Tests were not re-run.

### Exact next step

1. Step 1.2 (MLflow), shown to the owner for approval first.
2. These status changes reach main with the next pull request.

## Session 5 November 2026: agent harness plan

The agent parts of the plan were checked against current published sources on agent harnesses.

- Commit 521fd02: review and approval lines in the docs use group review wording. The
  architecture docs name the LangGraph agent graph.
- Commit 1709aba: one agent harness module in the plan (D38, R35): harness.py and
  configs/harness.yaml. Prompt token budget from 6.1, limits in 7.4, the new step 7.6 (tool
  list, allowed tools per route, basic safety rules, tool-call test on the Mac), chat history
  only in the chat tables of 1.10, request totals in traces (1.2) and cost per answer (2.3).
  Step 12.1 keeps the full rule tests. New FR-AGT-004, AT-7.6, the BFCL dataset, RISK-021
  and RISK-022. 20 docs follow the plan. Last updated date in 46 docs.
- No code, config or test files changed. Tests were not re-run.
- Check before Phase 1: plan version 1.10 in WORK_PLAN.md and 99 docs, 5 comments in 4 files,
  the current state row and R27. uv run pytest: 29 passed, 8 skipped. Verification numbers
  unchanged.

Notes for later steps:
- 7.6: tool calls of Qwen3.5-9B Q4_K_M on llama.cpp b11960 are not tested yet. The b11960
  source contains the parser that reads Qwen3.5 tool calls during thinking
  (common/parsers/qwen3-coder.cpp). The BFCL licence comes from its Hugging Face card and
  must be confirmed.
- 11.2: how the smolagents CodeAgent connects to llm_client.py is not checked yet.
- llama-server has experimental built-in tools (--tools). configs/llama-swap.yaml does not
  turn them on. Keep them off.

### Exact next step

1. Step 1.1 details in WORK_PLAN.md, docs/11-development-standards/git-workflow.md and
   CHANGELOG.md, shown to the owner for approval.
2. Phase 1, only after the owner says "start Phase 1".

## Session 4 November 2026: check and fixes

Full check of the repo, GitHub and the docs after the chat page plan.

- Mac tools upgraded for security fixes: uv 0.12.19 to 0.13.7 (advisory GHSA-hq85-5cpj-mr62)
  and rclone 1.73.1 to 1.75.2. uv sync, uv run pytest (29 passed, 8 skipped) and the
  verification numbers are unchanged.
- make backup 2026-11-04_010820: OK at commit 696d6d6. chat-preview is now on Drive. The run
  started before the rclone upgrade, so its log shows rclone v1.73.1.
- make restore-test 2026-11-04_015210: OK, all 7 checks, 4715 s.
- New backup rule (WORK_PLAN 15.1 item 5 and 6.4 rule 8): make backup and make restore-test
  at the end of the project or when the owner asks.
- Docs fixed: Q12 in the docs index, R1 to R34 in the traceability heading, first tag v0.0.0
  in the Git workflow, admin panel row in the screen specifications, database status line and
  the Last updated date of 62 docs.

Notes for later steps:
- Before the next backup: create an own Google Drive client_id for rclone. rclone says the
  shared client_id "will stop working during 2026" (rclone.org/drive, making your own client_id).
- pyproject.toml has uv_build>=0.12.19,<0.13.0. uv 0.13.7 still builds the project but warns.
- ops/backup.py: a backup stopped with Ctrl+C may still write result OK in its manifest
  (seen in the code, not tested).
- Step 1.10: admin panel features beyond user management are decided when 1.10 starts.

### Exact next step

1. Phase 1, only after the owner says "start Phase 1".

## Session 4 November 2026: chat page plan

The chat page preview (FastAPI, Jinja2, HTML, CSS and JavaScript, built outside this repo) was analysed.
Owner's decisions: rebuild it as platform code in the new step 1.10 with login (D37, R34). It was moved
from the repo folder to /Volumes/MacbookAPFS/Project/multiagent-ai-lab-local/chat-preview (outside Git,
included in make backup). WORK_PLAN.md and the docs were updated to match. New open question Q12.

Notes:
- The preview's .venv still points to its older copy on the Desktop. Run uv sync --reinstall in
  chat-preview before using it there. The Desktop copy still exists.
- Step 1.10: hash passwords as the OWASP Password Storage Cheat Sheet recommends (the preview uses scrypt
  with n=2**14, below that advice). Add a check against forged requests, delete expired sessions, fix the
  feedback not-found message (it uses the user message), remove the 700 ms wait in the page script and
  write the real tables into the data dictionary and the ER diagram.
- The preview has no saved tests. Step 1.10 adds them under tests/.

### Exact next step

1. Phase 1, only after the owner says "start Phase 1".

## Session 3 November 2026: check after Phase 0

Start-of-session checks passed (Qdrant had to be started again with docker compose up -d).
The full check of all files found 13 docs places that still showed Phase 0 in progress,
old test counts or old requirement status. They were missed at the end of Phase 0. All fixed,
see CHANGELOG.md [Unreleased].

Notes for later steps:
- Step 1.4: mypy reports transformers as missing when the demo group is not installed.
- Step 1.5: make pull-inbox has no test and was never run. Test it with the first Colab result.

### Exact next step

1. Phase 1, only after the owner says "start Phase 1".

## Session 2 to 3 November 2026: step 0.6

Step: 0.6 Backup and sync. Status: done.

### What was done

- Makefile and ops/backup.py: make backup, make restore-test (FULL=1 also downloads
  multiagent-ai-lab-local) and make pull-inbox. Target: My Drive/Project/MDU Offline Project.
- tests/unit/test_backup.py: 15 tests.
- Docs: WORK_PLAN.md D12, D13, D35, D36, Q2, sections 6.3 and 6.4. The same rules in 14 other docs.
- Verification numbers: ops/backup.py 13b6feaaa541, tests/unit/test_backup.py 0dda5947695d.
  All other files unchanged.

### Test results

| Run | Result |
|---|---|
| uv run pytest | 29 passed, 8 skipped |
| ruff 0.17.3 and mypy on ops | No issues |
| make backup | OK. 5,269 and 21,916 files, about 35.0 GB on Drive |
| make restore-test FULL=1 | All downloaded files match the SSD |
| make restore-test | OK, all 7 checks |

### Problems and fixes

- The first upload took about 17 hours (about 27,000 small files). Later runs upload only
  changed files (about 7 minutes).
- Run make restore-test right after make backup. Files created on the SSD after the backup
  count as differences.

### Deviations from the plan

None.

### Exact next step

1. Phase 1, only after the owner says "start Phase 1".

## Session 1 November 2026: step 0.5

Step: 0.5 Model client. Status: done.

### What was done

- src/mrag/llm_client.py: one client for all model calls (D34). get_client() reads the profile
  from .env and the roles from configs/models.yaml. Two backends:
  - openai_server (llama-swap on the Mac, vLLM on GPU later): chat, chat_stream, embed, rerank.
  - transformers (demo): chat and chat_stream. embed, rerank and JSON schema output give a
    NotSupportedError for now.
- Error types: ModelUnavailableError (server not reachable or timeout), InputTooLongError,
  ModelServerError (for example out of memory), NotSupportedError, all based on LLMError.
- Thinking is off unless a caller sets thinking=True. Reasoning text is returned separately.
- Typed results: ChatResult (text, reasoning, usage, finish_reason) and RerankResult.
- configs/models.yaml: profiles mac (llama-swap model IDs) and demo (Qwen/Qwen3.5-9B at revision
  c202236235762e1c871ad0ccb60c8ee5ba337b9a). Other profiles are added when their models are tested.
- Dependencies: openai 3.42.0 and pyyaml 6.0.3 (main), pytest 9.2.0 (dev group), transformers
  5.22.1, torch 2.15.0, torchvision 0.29.2 and pillow 13.0.0 (demo group, not installed by default).
- Test model for the transformers backend: Qwen/Qwen3.5-0.8B at revision
  2fc06364715b967f1860aea9cf38778875588b17 (Apache-2.0, about 1.8 GB in
  multiagent-ai-lab-local/hf-cache).
- Verification numbers: src/mrag/llm_client.py e7db46eb22ad, tests/unit/test_llm_client.py
  6c1d8f9a44c5, tests/integration/conftest.py 6d596db098e4, tests/integration/test_llm_client_mac.py
  91f740196030, tests/integration/test_llm_client_transformers.py 9292c4dcf0d8. Unchanged:
  src/mrag/__init__.py 3543b4693a36, src/mrag/config.py 24c7a5d4b87c, src/mrag/db.py 511eeaebbdbd,
  migrations/env.py c95357b4cf62, benchmarks/measure_mac.py 7c010b9ebef2. The SHA-256 of
  configs/models.yaml starts with 7fee9c963b19.

### How to run the tests

In Terminal, in /Volumes/MacbookAPFS/Project/multiagent-ai-lab, first load .env:

```
set -a
source .env
set +a
```

- All tests (the real-model tests skip themselves when their server or packages are missing):
  `uv run pytest`
- Mac model server tests: start llama-swap as described in the step 0.3 section, then
  `uv run pytest -m mac`
- Transformers backend tests: `uv run --group demo pytest -m transformers`

### Test results (coding assistant)

| Run | Result |
|---|---|
| uv run pytest | 14 passed, 8 skipped |
| uv run pytest -m mac (llama-swap running) | 7 passed: text, stream, thinking switch, image, JSON schema, embedding, rerank |
| uv run python -m mrag.llm_client | "mac profile answered: ready" |
| uv run --group demo pytest -m transformers | 3 passed: text, stream, image |
| Thinking mode in the transformers backend (checked by hand) | Answer "5", reasoning returned separately |
| mypy on src/mrag | No issues |
| ruff 0.17.3 (default rules) on src and tests | All checks passed |

### Problems and fixes

- The Qwen image processor in transformers needs Pillow and torchvision. transformers does not
  install them, so both are in the demo group.
- mypy and ruff found three small points (an unused variable in a test, the type of the rerank
  answer, transformers type hints for model.to). All fixed.
- macOS Finder writes .DS_Store files into .venv. When uv removes the demo packages, folders with
  only these files stay behind and Python sees an empty transformers package. Fix: the
  transformers test skips unless transformers 5.22.1 or newer is really installed (minversion).

### Deviations from the plan

- The transformers backend does chat only. Embedding and reranking for it come with the retrieval
  work of the demo (steps 1.8 and 5.x). JSON schema output is not available in it.
- embed() takes text only. Image embeddings are designed in step 5.2.

### Notes for later steps

- Step 1.4: ruff 0.17.3 reports 9 style points in benchmarks/measure_mac.py (subprocess.run without
  check, one open() without a with block, two newer spellings). Fix them with the project's ruff
  rules.
- Step 1.2: confirm that MLflow tracing works with openai 3.x.
- Step 1.8: on the demo GPU, the fast kernels for Qwen3.5 (causal_conv1d, flash-linear-attention)
  can replace the slower PyTorch fallback that the Mac uses.
- End of Phase 0: update the status banner in the 99 docs and docs/README.md (it still says only
  the step 0.1 setup exists as code).

### Exact next step

Next session (connect the SSD first, then start Docker Desktop):
1. Step 0.6 Backup and sync: rclone with Google Drive, multiagent-ai-lab-backup with backup/ and
   inbox/, make backup, make pull-inbox and make restore-test, the rules of section 6.4 in the
   docs, decide Q2. Ask the owner before writing any file (rule C3).

## Session 31 October to 1 November 2026: step 0.4

Step: 0.4 Measure the Mac. Status: done.

### What was done

- Smaller model variants made from the official weights already on the SSD (no download):
  Q4_K_M of the embedding and reranker models (through an F16 file and llama-quantize) and
  Q8_0 image parts. All in multiagent-ai-lab-local/models. The Q4_K_M reranker keeps
  pooling_type 4 (rank), the classifier labels and cls.output.weight.
- benchmarks/measure_mac.py: starts llama-server for each scenario, runs a fixed workload
  (streamed chat without thinking, one image question, 16 text pieces and one image for the
  embedding model, one question against 20 documents and one image for the reranker), samples
  wired memory twice per second, reads each server's total memory with footprint and writes
  results/p0_resources.csv.
- src/mrag/config.py: new settings llama_server and models_dir (from MRAG_LLAMA_SERVER and
  MRAG_MODELS_DIR in .env).
- configs/llama-swap.yaml: measured settings (D33). Main, embedding and reranker in the group
  "rag" (loaded together). The helper in its own group swaps with them.
- Verification numbers: src/mrag/__init__.py 3543b4693a36, src/mrag/config.py 24c7a5d4b87c,
  src/mrag/db.py 511eeaebbdbd, migrations/env.py c95357b4cf62, benchmarks/measure_mac.py
  7c010b9ebef2. The verification command now also lists the benchmarks folder. The SHA-256 of
  configs/llama-swap.yaml starts with 8e64339f8d6e.

Commands for the variants (from multiagent-ai-lab-local/tools/llama.cpp-src-b11960, shown for
the reranker, the embedding model is the same with its own snapshot folder and names):

```
HF_HUB_OFFLINE=1 ../llama-convert-venv/bin/python convert_hf_to_gguf.py <snapshot folder> --outtype f16 --outfile ../../models/Qwen3-VL-Reranker-2B-F16.gguf
../llama.cpp-b11960/llama-quantize ../../models/Qwen3-VL-Reranker-2B-F16.gguf ../../models/Qwen3-VL-Reranker-2B-Q4_K_M.gguf Q4_K_M
HF_HUB_OFFLINE=1 ../llama-convert-venv/bin/python convert_hf_to_gguf.py <snapshot folder> --mmproj --outtype q8_0 --outfile ../../models/mmproj-Qwen3-VL-Reranker-2B-Q8_0.gguf
```

### How to run the measurement

Close browsers and other large apps. In Terminal, in /Volumes/MacbookAPFS/Project/multiagent-ai-lab:

```
set -a
source .env
set +a
uv run python benchmarks/measure_mac.py
```

It takes about 15 minutes and overwrites results/p0_resources.csv.

### Test results (run on 31 October 2026, commit d3c54be, llama.cpp b11960, GPU limit 12124 MB)

| Scenario | Status | Peak wired increase | Speed |
|---|---|---|---|
| Main alone, ctx 8192 | ok | 6983 MB | First token 0.42 s, 14.6 tokens/s, image answer 3.4 s |
| Main alone, ctx 32768 | ok | 7757 MB | First token 0.41 s, 14.1 tokens/s |
| Helper alone, ctx 4096 | ok | 2242 MB | First token 0.11 s, 40.2 tokens/s |
| Embedding alone, Q8_0, image F16, ctx 4096 | ok | 3996 MB | 7.4 s |
| Reranker alone, Q8_0, image F16, ctx 8192 | ok | 4158 MB | 11.3 s |
| Main + embedding Q8_0 + reranker Q8_0, images Q8_0 | out of memory | 12055 MB | - |
| Main + embedding Q4_K_M + reranker Q4_K_M, images Q8_0 | ok | 11839 MB | Embedding 8.3 s, reranking 12.8 s |
| Main + embedding Q4_K_M + reranker Q4_K_M text only | ok | 10968 MB | Chat 14.7 tokens/s, embedding 8.3 s, reranking 12.2 s |

Extra test through llama-swap with the chosen settings and a full page image (1240 x 1754):
the embedding model and the main model both handled the page, peak wired increase 10738 MB,
no out-of-memory error. The 5 test calls of step 0.3 pass with the new settings. Embedding
similar 0.891 and unrelated 0.26. Reranking keeps the correct document first (0.686).

### Problems and fixes

- llama-server picks a new image placeholder at every start. Its README still shows the old
  fixed one. The script reads the current placeholder from /props (media_marker).
- A full page image needs about 2150 tokens, more than the embedding context of 2048. Fix:
  --image-max-tokens 1280, the image limit in the model's own preprocessor_config.json.
- Swap use grew from 1.5 GB to 3.9 GB during the out-of-memory scenario. macOS released it
  slowly afterwards.

### Deviations from the plan

- The reranker runs text only next to the other two models. Step 5.4 planned image reranking.
  To be revisited in 5.4 (for example a separate image reranker that swaps in when needed).
- The quality of the Q4_K_M embedding and reranker models is not measured yet. Step 5.5.
- The helper cannot stay loaded with the other three models (all four do not fit). Phase 7
  decides whether the helper is kept.
- The scenario "current settings together" was not repeated. Step 0.3 already showed it runs
  out of memory.
- New top-level folder benchmarks/ for tools that are not platform code (rule C2, section 8.2).
- Step 0.7 marked done in the same session: docs/WORK_PLAN.md is on GitHub and shows Phase 0 progress.

### Notes for later steps

- Reranking costs about 0.6 s per document on the Mac. Phase 5 sets how many candidates are
  reranked.
- A larger main context is cheap: ctx 32768 costs about 0.8 GB more than ctx 8192 (step 6.2).
- The margin to the GPU limit is about 1.3 GB. Other large GPU apps can still cause an
  out-of-memory error.
- The F16 files of the embedding and reranker models stay in multiagent-ai-lab-local/models for
  other quantisations later.

### Exact next step

Next session (connect the SSD first):
1. Step 0.5 Model client: llm_client.py, one wrapper for all model calls (OpenAI-style server
   on the Mac and on GPU, Transformers for the demo), chosen by profile. Ask the owner before
   writing any file (rule C3).

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
- Owner's decision D28 and new rule C14: no product comparisons in the repo. All 31 places in
  README.md and docs/ (13 files) now describe the real feature instead. The banned words appear
  only inside rule C14 and decision D28, which name them in order to ban them.
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

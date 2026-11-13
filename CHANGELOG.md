# Changelog

All notable changes to this project are listed here, newest first.
Versions are tagged at the end of each phase (WORK_PLAN.md rule G).

## [Unreleased]

### Added

- API under /v1 (src/mrag/api.py with FastAPI, started with make api on 127.0.0.1:8000): health, version (package, profile, git commit and pipeline version), models of the active profile from configs/models.yaml and a chat endpoint that streams the events of harness.run() as Server-Sent Events. Experimental until the API is frozen. src/mrag/service.py holds the functions and the route table. Requests are traced only while the MLflow server answers. A unit test reads the imports and fails if service.py, api.py or a route agent creates a model client or reaches the search or a tool directly or if the harness imports them.
- harness.run(): the only entry of the agent harness. It streams the answer pieces of a route and ends with the full answer and the request totals or with an error event, within the answer token cap and the time limit of the profile. Every step runs in one context, so the request trace keeps its totals when a web server reads each step in another thread.
- Agent harness settings per profile (configs/harness.yaml) and context building (src/mrag/harness/): the system prompt, the new message and as many of the newest earlier turns as fit the token budget of the profile, counted exactly with the pinned Qwen3.5 tokenizer. CI downloads the tokenizer and checks its SHA-256. fastapi, uvicorn and tokenizers are direct dependencies.
- Plan for the API-first skeleton (D45): FastAPI under /v1 with health, version, models and a chat endpoint that streams Server-Sent Events from harness.run(), the chat history within a token budget per profile counted exactly with the pinned Qwen3.5 tokenizer and settings per profile in configs/harness.yaml.
- Plan and docs: the free GPU profile is done. vLLM serves the gpu profile on Kaggle and llama.cpp runs on Colab, chosen from the measured smoke test results. Qwen3.8-27B in 4-bit is tested and kept outside the profile. The results, failed tries and GPU hours are in docs/HANDOVER.md.
- gpu profile in configs/models.yaml: Qwen3.5-9B in 16-bit served by vLLM 0.33.0 on Kaggle's 2 x T4, the candidate chosen from the GPU smoke test results. A unit test keeps it in line with configs/gpu_candidates.yaml. GPU smoke test runs now record only the model of their candidate. ops/check_result.py checks such a run against its candidate in configs/gpu_candidates.yaml instead of the profile.
- GPU smoke test: a Kaggle candidate that runs Qwen3.8-27B in 4-bit (Red Hat's W4A16 weights) with vLLM, because vLLM answered faster than llama.cpp for Qwen3.5-9B on Kaggle's 2 x T4 (median 39.4 against 23.4 tokens per second on five fixed questions). The cache of attention keys and values stays 16-bit, because vLLM 0.33.0 allows the model's 8-bit fp8 cache only on newer GPUs than the T4. The smoke test now passes this setting to vLLM. Both weight files of the model are downloaded, because vLLM 0.33.0 does not start when a file named in the model's weight index is missing. When a model server stops, the smoke test now also shows the first error lines of its log, because with 2 GPUs a vLLM worker's error can come long before the end.
- CI's pip-audit accepts three setuptools advisories for the vLLM lock only (vLLM 0.33.0 requires setuptools below 81): one hole in making source packages (listed under two IDs) and one hole on Windows only. Neither can affect the vLLM environment, which runs on Linux, is installed from ready-made wheels and makes no source packages. The reasons are in ci.yml. A unit test fails as soon as the lock has a setuptools that fixes one of them, so that exception must then be removed.
- GPU notebooks for Kaggle (notebooks/kaggle_gpu.ipynb) and Colab (notebooks/colab_gpu.ipynb), every cell labelled: they check the GPUs, driver, disk and memory, install uv 0.13.7, get the code at a chosen commit, install the platform from uv.lock and vLLM from its own lock, run the GPU smoke test and copy the result bundle to the notebook output (Kaggle) or the Drive inbox (Colab). vLLM 0.33.0 now has its own locked environment (ops/vllm-server, Linux only), checked by pip-audit in CI and watched by Dependabot. The smoke test now stops before any download when the NVIDIA driver is too old for the server or the files would not fit on the disk. A unit test checks both notebooks.
- GPU smoke test (ops/gpu_smoke.py) for Kaggle and Colab: downloads one candidate from configs/gpu_candidates.yaml with SHA-256 checks and resume, starts llama.cpp or vLLM, asks five fixed public questions and records correct answers, time to first token, tokens per second, load time and GPU hours as one MLflow run in a database file in the gpu profile. Each answer is saved at once, so a disconnected job continues where it stopped. The run is written as a result bundle, which ops/import_runs.py adds to the Mac's MLflow once (make pull-inbox). The Colab vLLM candidate now loads the official weights as 8-bit fp8 instead of bitsandbytes, which vLLM 0.33.0 no longer has built in.
- configs/gpu_candidates.yaml: the server builds and model files the GPU smoke test may use on Kaggle and Colab, each pinned by version or revision and SHA-256, with a unit test.
- GitHub settings: GitHub's secret scanning with push protection, Dependabot security updates and both CI checks required in protect-main, with the branch up to date with main. A deliberately failing test on a short-lived branch turned CI red and its pull request to main was blocked.
- Dependabot (.github/dependabot.yml): weekly pull requests for newer Python packages in both uv lock files, GitHub actions and the Qdrant image, with a 7-day wait for new releases and minor and patch updates grouped. It starts once the file is on main.
- Evaluation gate (ops/eval_gate.py), run by CI on every push: the newest published result of each route, profile and dataset in results/ must meet its minimum or maximum in configs/eval/limits.yaml. A missing or broken score fails. No limits yet, so it passes and says so.
- CI runs one real model test: llama.cpp b11960 (the same server program as on the Mac) serves Qwen3.5-0.8B on the CPU and llm_client.py asks it a question, normally and streamed. The model is pinned in the new ci profile of configs/models.yaml. Both downloads are checked against their SHA-256 on every run and cached between runs.
- CI on GitHub Actions (.github/workflows/ci.yml): ruff, formatting, mypy, pip-audit on both lock files and the unit tests on every push and pull request to main, on a free standard runner with actions pinned to commit IDs.
- Code checks: ruff (style and common mistakes, line length 100, automatic formatting), mypy (strict checks for the platform package) and pip-audit (known security holes), pinned in the dev group. One crash risk when recording a stopped model call is fixed.
- ops/check_result.py traces one MLflow run to its exact versions: git commit, config and prompt files at that commit, MLflow prompt versions, pinned model files and the pipeline version.
- Pipeline version: one fingerprint of the code version (commit and uncommitted changes), profile, config files (with the model revisions) and prompt files, stored on every run and trace and in the dashboard export.
- prompts.py loads prompts from configs/prompts/<name>.txt and registers each changed text as a new MLflow prompt version. Every use is recorded in the trace and the run. Without MLflow the version is the file's fingerprint.
- Mac models pinned in models.yaml with source, revision and the SHA-256 of every file the model server loads. Runs record them. A unit test keeps llama-swap.yaml and models.yaml in line. A Mac test checks the files.
- MLflow 3.17.2: the mlflow-skinny client for the platform and the full mlflow package in its own locked environment in ops/mlflow-server for the local server.
- make mlflow starts the local MLflow server on the address in MRAG_MLFLOW_TRACKING_URI, with its data in mlflow/ and usage statistics turned off. It only accepts an address on this Mac.
- tracing.py: one MLflow trace per request with its totals (tokens in and out, model calls, tool calls, time and the fallback used), one span per model call and experiment runs with the git commit, config fingerprints, model and dataset versions, metrics and result files. On in the mac profile only.
- llm_client.py records every chat, streamed chat, embedding and rerank call inside a request with its model, inputs, answer, time and tokens. Streamed answers now report their token counts.
- export_results.py writes a JSON summary of every published MLflow run into results/<route>/<date>_<run id>.json for the dashboard: metrics, versions and git commit only, each run once. Runs are published only when marked for public test sets.
- make backup also takes a clean copy of the MLflow database. make restore-test checks its integrity and that MLflow opens it.
- Mac test with the real model server and MLflow server: one request trace with its tokens and model calls. One run with its result file.

### Changed

- GPU smoke test: the model server now gets a free port chosen by the operating system instead of the fixed port 8080, which another program already used on Colab, so llama-server could not start there. The GPU notebooks now show the output of every program they run, which Colab did not show before, so a failure shows its reason in the notebook. Unit tests cover both.
- GPU smoke test: both vLLM candidates now allow at most 16 requests at once (max_num_seqs in configs/gpu_candidates.yaml). On Kaggle's 2 x T4, vLLM 0.33.0 refused to start Qwen3.5-9B with its default of 256, because Qwen3.5 needs one state block per running request and only 217 fit. When a server stops or is not ready in time, the error now shows the last 100 lines of its log. The progress lines now appear in the notebook at once.
- Plan: the GPU profile server and results (D44). The smoke test compares vLLM and llama.cpp b11960 on Kaggle and the measured results decide. GPU jobs save checkpoints and write result bundles, which make pull-inbox imports into the Mac's MLflow through ops/import_runs.py.
- Plan: Kaggle free (2 x T4, 32 GB) is the main cloud GPU and Google Colab free (1 x T4) the backup for jobs that fit 16 GB (D10). The GPU profile models fit the GPU memory: Qwen3.5-9B in full 16-bit and Qwen3.8-27B in 4-bit on Kaggle, Qwen3.5-9B in 8-bit on the Colab backup (D11). The docs follow the plan.
- Plan: model work at upload stays outside the agent harness (figures.py, sections.py and kg.py call the model client directly), the injection classifier becomes an engine (injection.py), sections.py makes the section summaries at upload and the import test of the harness starts with the first chat endpoint. The models endpoint reads configs/models.yaml. R35 names every harness part. The handover records the harness redesign.
- Plan: the agent harness becomes one package, src/mrag/harness/ (D43, replaces D38). It holds context building, retrieval at question time, memory, tools, the agent loop, limits, guards, answer checks and the request trace totals behind one entry, harness.run(), which streams answer events from the first chat endpoint on. Rule C2 allows this one package. New: a harness check (an import test and a part-by-part ablation), the requirement FR-AGT-005 and the risk RISK-023. The design is described in docs/04-architecture/agent-harness.md. The docs follow the plan.
- Python is pinned to 3.12.16 (the newest 3.12 security release) for the platform and the MLflow server, so the Mac, CI and every other computer use exactly the same Python.
- Plan: CI pipeline (D42). Standard runners in the public repo only, no stored artifacts, a real model test with llama.cpp and Qwen3.5-0.8B, GitHub's secret scanning with push protection, Dependabot and CI required on main.
- compose.yaml pins the Qdrant image by digest as well as by version tag.
- Plan: versioning rules (D41). Prompts as text files in Git registered in the MLflow prompt registry, a pipeline version ID on every run and trace, models pinned with source, revision and file SHA-256, datasets pinned by revision and file hash from 2.1 and Qdrant pinned by image digest.
- Plan: MLflow 3.17.2 runs natively on the Mac through uv with its data in mlflow/ (D40). Model calls are traced from now on, LangGraph steps from 7.2. Usage telemetry is off. The deployment docs follow the plan.

## [0.0.1] - 2026-11-05

### Added

- GitHub workflow: the ruleset protect-main protects main (pull request required, no deletion, no force push, no bypass). Pull requests are merged with merge commits only. Work happens on one branch per phase.

### Changed

- Plan: GitHub workflow (D39): ruleset protect-main on main, pull requests with merge commits only, one branch per phase and the gh command-line tool. The Git workflow doc and AT-1.1 follow the plan.
- WORK_PLAN.md v1.10. The docs link to it.
- Plan: one agent harness module, harness.py with configs/harness.yaml (D38, R35). Prompt token budget per profile from step 6.1, request limits in 7.4, the new step 7.6 for the tool list, the allowed tools per route and the basic safety rules, chat history only in the chat tables of 1.10, request totals in every trace from 1.2 and cost per answer in 2.3. Step 12.1 keeps the full rule tests. New FR-AGT-004, AT-7.6, the BFCL dataset, RISK-021 and RISK-022. The docs follow the plan.
- Plan: own chat web page with accounts and login in the new step 1.10 (D37, R34). Rule A, sections 6.3, 8.1, 8.2 and 9 and steps 12.4 to 13.3 match it. New open question Q12 (MCP tool). The docs follow the plan.
- WORK_PLAN.md 15.1 and 6.4: make backup and make restore-test at the end of the project or when the owner asks.

### Fixed

- Comments in .env.example, .gitignore, pyproject.toml and src/mrag/__init__.py describe the reason in plain words.
- WORK_PLAN.md: last completed step in the current state table. R27 covers the plan file only.
- Docs: review and approval lines in the decision records, the requirement documents and the docs index use group review wording. The architecture docs name the LangGraph agent graph.
- Last updated date in 46 docs.
- docs/README.md and srs.md: requirement status lines now match the requirement documents.
- Login before step 1.10 in the docs index, access policy, authentication, endpoint catalog, risk register and traceability.
- docs/README.md: status line now lists what exists as code.
- WORK_PLAN.md: download folder path in the project setup text (D31).
- Phase 0 status corrected in README.md, the docs index, project overview, roadmap, milestones, acceptance test cases, testing status and database design.
- Requirement status: FR-OPS-004, NFR-PERF-001, NFR-PORT-001, NFR-SEC-005, R12, R13, R28 and R33.
- WORK_PLAN.md and project-structure.md: ops/ folder in the repo structure.
- docs/README.md: open questions now include Q12.
- Requirement range in the traceability heading, first tag in the Git workflow, admin panel row in the screen specifications and the database status line.
- Last updated date in 62 docs.

## [0.0.0] - 2026-11-03

### Added

- Step 0.6: `Makefile` (make backup, make restore-test, make pull-inbox), `ops/backup.py` (both
  project folders on the SSD to Google Drive with rclone, dated history, Qdrant snapshot, SQLite
  copy, restore test), 15 tests in `tests/unit/test_backup.py`.
- Step 0.5: `src/mrag/llm_client.py` (one client for all model calls, backends openai_server
  and transformers), `configs/models.yaml`, 24 tests. Dependencies: openai, pyyaml, pytest (dev),
  transformers, torch, torchvision, pillow (demo group).
- Step 0.4: `benchmarks/measure_mac.py` (memory and speed of the local models),
  `results/p0_resources.csv`, settings `llama_server` and `models_dir` in `config.py`.
  `configs/llama-swap.yaml`: measured settings, main, embedding and reranker loaded together.
- Step 0.3: `configs/llama-swap.yaml` (4 models, one at a time, port 8080 on this Mac only).
  `.env.example`: new HF_HOME path, MRAG_LLAMA_SERVER and MRAG_MODELS_DIR.
- Step 0.2: `compose.yaml` with Qdrant v1.20.0 (port 6333 on this Mac only, data in a Docker volume,
  usage statistics off).
- Step 0.1: uv project with Python 3.12, package `mrag` in `src/`,
  `config.py` (settings and profiles), `db.py` (SQLAlchemy, SQLite), Alembic migrations,
  `.gitignore`, `.env.example`, Apache-2.0 licence, README and docs/HANDOVER.md.

### Changed

- Status line at the top of 99 docs: Phase 0 done.
- WORK_PLAN.md: decisions D12, D13, D35 and D36, Q2, sections 6.3 and 6.4, step 0.6 text and
  status. The same backup rules in 14 other docs.
- WORK_PLAN.md: decision D34 (model client) and step 0.5 status.
- WORK_PLAN.md: step 0.7 status (its test passes). HANDOVER.md: wording fix (rule C14).
- WORK_PLAN.md: decision D33 (Mac model settings), rule C2, repo structure and step 0.4 status.
- WORK_PLAN.md: decisions D31 (large local files in multiagent-ai-lab-local) and D32 (model server
  versions and model sources), storage table and step 0.3 status.
- WORK_PLAN.md: decision D30 (Qdrant data in a Docker volume), storage table and step 0.2 status.
- WORK_PLAN.md v1.8: decisions D23 to D27, open questions Q1 and Q8 answered, step 0.1 status.
  All docs updated to match.
- WORK_PLAN.md v1.9: product comparisons replaced by descriptions of the real features
  (decision D28, new rule C14).
- README.md description replaced by "Work in Progress" until features exist.
- WORK_PLAN.md: no assistant product names in repo files (decision D29, new rule C15).
  Repo history started again with one fresh commit.

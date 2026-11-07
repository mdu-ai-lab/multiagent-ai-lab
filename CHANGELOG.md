# Changelog

All notable changes to this project are listed here, newest first.
Versions are tagged at the end of each phase (WORK_PLAN.md rule G).

## [Unreleased]

### Added

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
- Mac test with the real model server and MLflow server: one request trace with its tokens and model calls, and one run with its result file.

### Changed

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

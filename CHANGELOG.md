# Changelog

All notable changes to this project are listed here, newest first.
Versions are tagged at the end of each phase (WORK_PLAN.md rule G).

## [Unreleased]

### Added

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

# Backup and recovery

| Field | Value |
|---|---|
| Purpose | How work is protected and restored |
| Status | Proposed |
| Last updated | 2026-11-05 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Data privacy](../07-security/data-privacy.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

WORK_PLAN.md sections 6.3 and 6.4 are copied word for word below. They are the only backup rules.

Plan gap: the knowledge graph store (Phase 9A) and notebook data (Phase 9B) are not listed in section 6.3 or 6.4. Their storage and backup layer: REQUIRES CONFIRMATION.

## Storage layout on the SSD (WORK_PLAN.md section 6.3, word for word)

| Path | Content | In Git | Backed up to Drive |
|---|---|---|---|
| /Volumes/MacbookAPFS/Project/multiagent-ai-lab/ | The Git repo (code, configs, docs, tests, notebooks, exported results) | Yes | Yes (whole folder, D35) |
| .../multiagent-ai-lab/data/private/ | Private documents | No | Yes |
| .../multiagent-ai-lab/data/public/ | Public datasets | No | Yes |
| .../multiagent-ai-lab/data/annotations/ | Hand-made labels, golden insights, human judge checks | Yes (small text) | Yes |
| .../multiagent-ai-lab/mlflow/ | MLflow database and artifacts | No | Yes |
| Docker volume multiagent-ai-lab_qdrant_data (inside Docker Desktop's disk image on the SSD, see D30) | Search index | No | Yes (full Qdrant snapshot) |
| .../multiagent-ai-lab/results/ | Exported result summaries for the dashboard | Yes | Yes |
| /Volumes/MacbookAPFS/Project/multiagent-ai-lab-local/hf-cache/ | Downloaded model files (HF_HOME) | No | Yes |
| .../multiagent-ai-lab-local/models/ | Embedding and reranker GGUF files converted locally (D32) | No | Yes |
| .../multiagent-ai-lab-local/tools/ | llama.cpp b11960, llama-swap v268, the llama.cpp converter source and its Python environment (D32) | No | Yes |
| .../multiagent-ai-lab-local/chat-preview/ | Chat page preview (FastAPI, Jinja2, HTML, CSS and JavaScript), the source for step 1.10. Its own database and uploads stay here | No | Yes |
| /Volumes/MacbookAPFS/Project/.uv-cache/ | uv cache (set by UV_CACHE_DIR in ~/.zshrc, see D27) | No | No |
| /Volumes/MacbookAPFS/Project/docker-data/ | Docker Desktop disk image (already on the SSD) | No | No (Qdrant goes as a snapshot) |

Docker Desktop auto-start is off. Connect the SSD before starting Docker.

## Backup and working without the SSD (section 6.4, word for word)

make backup copies the whole project on the SSD to Google Drive (D35). It is a backup, not a working folder: a Git repo, SQLite or Qdrant files must never run inside a synced folder, because sync tools can corrupt them or create conflict copies.

The approach has 3 layers:

| Layer | What | Where | How it is restored |
|---|---|---|---|
| 1. Git | Code, configs, docs, notebooks, tests, small annotations, exported results, this plan | GitHub (public repo) | git clone |
| 2. Drive backup | Both project folders on the SSD, a Qdrant snapshot and clean SQLite copies of the app and MLflow databases | Google Drive: My Drive/Project/MDU Offline Project/ (exact copy of each folder plus multiagent-ai-lab-backup/ with dated history/ folders) | rclone copy back to the SSD or another disk |
| 3. Re-creatable | uv cache, Docker images | Not backed up | uv sync and docker compose pull |

Rules that prevent lost files and conflicts:

| # | Rule |
|---|---|
| 1 | GitHub is the only source of truth for code and docs. Google Drive never holds a working copy of the repo |
| 2 | One active machine at a time. Before switching: commit and push. On the other machine: pull first |
| 3 | Work done in Colab goes to a branch named remote/YYYY-MM-DD. Merge it on the Mac through a pull request so CI checks it |
| 4 | Result files are written once with unique names (run ID + date). They are never edited in two places |
| 5 | Drive backup is one-way (rclone sync to the copy of each folder. Every changed or deleted file moves to a dated history/ folder). Nothing on Drive is deleted. No two-way sync |
| 6 | Colab results go to Drive multiagent-ai-lab-backup/inbox/. On the Mac, make pull-inbox copies new files only (never overwrites) and imports them into MLflow |
| 7 | Check Drive usage monthly. The owner's Drive has 2 TB |
| 8 | Restore test (make restore-test) right after each make backup: checksum of every file, restore into a temporary folder, Qdrant snapshot and SQLite checks. From step 1.2 also check that MLflow opens |
| 9 | Secrets (GitHub token, Hugging Face token) live in GitHub Secrets, Colab Secrets and your password manager. Never in Git or Drive |

When the SSD is lost or broken, restore the backup to another SSD or laptop (docs/10-deployment-and-operations/backup-and-recovery.md). What you can do when the SSD is unavailable: write and test code, run public-data experiments on Colab and update docs. Private-document work waits until the SSD is back.

Tools: Git (free), rclone (free, open source) on the Mac, the built-in Google Drive mount in Colab. Google Drive for Desktop is not needed.

## How to run the backup

Connect the SSD and start Docker Desktop (Qdrant must run for its snapshot). In Terminal:

```
cd /Volumes/MacbookAPFS/Project/multiagent-ai-lab
make backup
make restore-test
```

Run make restore-test right after make backup: files changed in between show up as differences. make restore-test FULL=1 also downloads the 33 GB folder multiagent-ai-lab-local into a temporary folder. make pull-inbox copies new Colab results from the inbox to data/inbox/ and never overwrites a file.

The code is in ops/backup.py. Layout on Google Drive:

```
My Drive/Project/MDU Offline Project/
├── multiagent-ai-lab/            exact copy of the repo folder (with .git, .env, data/ and .venv)
├── multiagent-ai-lab-local/      exact copy of the models and tools folder
└── multiagent-ai-lab-backup/
    ├── history/<run>/            files that changed or were deleted since the run before
    ├── logs/<run>/               manifest.json and the rclone logs of each run
    ├── snapshots/                qdrant-full.snapshot (+ .sha256), app.db and mlflow.db (clean SQLite copies)
    └── inbox/                    Colab results
```

Other folders in MDU Offline Project are never touched. Every Drive path the script writes to is checked to be one of the folders above.

What make backup does:

| Part | How |
|---|---|
| Safety check | Stops if the SSD is missing or a folder looks incomplete (.git, pyproject.toml, src/mrag, hf-cache, models, tools). Only one backup or restore test runs at a time |
| Qdrant | Full snapshot through the Qdrant API, downloaded, checked against Qdrant's SHA-256 and then deleted inside Qdrant. If Qdrant is not running the summary says SKIPPED and the last snapshot on Drive stays |
| SQLite | Clean copies of data/app.db and mlflow/mlflow.db with SQLite's own backup function. The source is opened read-only. The copy must pass PRAGMA integrity_check |
| Both folders | rclone sync with --backup-dir (old versions to history/), --links (symbolic links stay links), -M (file permissions, for example the executable mark of llama-server) and --create-empty-src-dirs |
| Not copied | hf-cache/token and hf-cache/stored_tokens (login tokens, rule 9) and multiagent-ai-lab-local/backup-logs/ (already in multiagent-ai-lab-backup/logs/) |
| Tracking | manifest.json per run: time, duration, Git commit and branch, uncommitted changes, rclone version, files and bytes per folder, Qdrant and SQLite results, Drive usage and errors. A copy stays in multiagent-ai-lab-local/backup-logs/<run>/ |

What make restore-test checks:

| Check | How |
|---|---|
| Drive copy matches the SSD | rclone check of every file by MD5 checksum, without downloading |
| Restored copy matches the SSD | Downloads multiagent-ai-lab (and with FULL=1 also multiagent-ai-lab-local) into /Volumes/MacbookAPFS/Project/.restore-test-<run>/ and compares every file |
| Qdrant | Snapshot checksum, then a temporary Qdrant (port 6334) starts from the snapshot. Its collections and point counts must equal the live Qdrant. SKIP when Docker is off |
| SQLite | PRAGMA integrity_check on both clean copies and on the restored data/app.db and mlflow/mlflow.db. MLflow must open the copy of its database |
| Drive usage | rclone about and rclone size of the three folders, saved in restore-test.json |

The temporary folder is deleted at the end.

## How to restore on another laptop or SSD

Needs a Mac with an Apple chip (the downloaded llama.cpp and llama-swap programs are built for it). On another computer type, download those programs again for that computer.

1. Install Homebrew, then rclone, uv and Docker Desktop. Connect rclone to the Google account: `rclone config`, new remote named gdrive, type drive, scope drive, Shared Drive: n.
2. Name the new SSD MacbookAPFS and create /Volumes/MacbookAPFS/Project. With another name or folder, change the paths in .env (HF_HOME, MRAG_LLAMA_SERVER, MRAG_MODELS_DIR) after the copy.
3. Copy everything back:

```
rclone copy "gdrive:Project/MDU Offline Project/multiagent-ai-lab" /Volumes/MacbookAPFS/Project/multiagent-ai-lab --links -M --create-empty-src-dirs --progress
rclone copy "gdrive:Project/MDU Offline Project/multiagent-ai-lab-local" /Volumes/MacbookAPFS/Project/multiagent-ai-lab-local --links -M --create-empty-src-dirs --progress
rclone copy "gdrive:Project/MDU Offline Project/multiagent-ai-lab-backup/snapshots" /Volumes/MacbookAPFS/Project/restore-snapshots
```

4. Rebuild the Python environment (the copied .venv points to the old Python install). Add `export UV_CACHE_DIR=/Volumes/MacbookAPFS/Project/.uv-cache` to ~/.zshrc (D27) first:

```
cd /Volumes/MacbookAPFS/Project/multiagent-ai-lab
rm -rf .venv
uv sync
```

5. Restore Qdrant into its Docker volume. The first command loads the snapshot. Wait until `curl -s http://127.0.0.1:6333/healthz` prints "healthz check passed", then stop it and start Qdrant normally:

```
docker run -d --rm --name qdrant-restore -p 127.0.0.1:6333:6333 -v multiagent-ai-lab_qdrant_data:/qdrant/storage -v /Volumes/MacbookAPFS/Project/restore-snapshots:/restore:ro qdrant/qdrant:v1.20.0 ./qdrant --storage-snapshot /restore/qdrant-full.snapshot
docker stop qdrant-restore
docker compose up -d
```

6. Check: `uv run python -m mrag.config` prints the settings and `uv run pytest` passes. Then delete /Volumes/MacbookAPFS/Project/restore-snapshots.

The data/app.db inside the copied repo folder is the live file at backup time. If its integrity check fails, use app.db from restore-snapshots instead.

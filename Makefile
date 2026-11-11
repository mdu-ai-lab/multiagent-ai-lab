# Project commands. Run them from the repo folder, for example: make backup
# The backup copies the whole project on the SSD to Google Drive with rclone.
# Details: docs/10-deployment-and-operations/backup-and-recovery.md

.PHONY: backup restore-test pull-inbox mlflow

# Copy the repo folder and multiagent-ai-lab-local to Drive, plus a Qdrant snapshot
# and clean SQLite copies of the app and MLflow databases. Changed or deleted files are kept in a dated history folder
backup:
	uv run python ops/backup.py backup

# Check the copy on Drive against the SSD and restore it into a temporary folder.
# make restore-test FULL=1 also downloads the 33 GB models folder
restore-test:
	uv run python ops/backup.py restore-test $(if $(FULL),--full)

# Copy new files from the Drive inbox (Colab results) to data/inbox. Never overwrites.
# Then add the result bundles in data/inbox to MLflow, each once (needs make mlflow)
pull-inbox:
	uv run python ops/backup.py pull-inbox
	uv run python ops/import_runs.py

# Start the local MLflow server in this terminal (address from MRAG_MLFLOW_TRACKING_URI).
# Stop it with Ctrl+C. Its data stays in the mlflow folder
mlflow:
	uv run python ops/mlflow_server.py

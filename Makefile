# Project commands. Run them from the repo folder, for example: make backup
# The backup copies the whole project on the SSD to Google Drive with rclone.
# Details: docs/10-deployment-and-operations/backup-and-recovery.md

.PHONY: backup restore-test pull-inbox

# Copy the repo folder and multiagent-ai-lab-local to Drive, plus a Qdrant snapshot
# and a clean SQLite copy. Changed or deleted files are kept in a dated history folder
backup:
	uv run python ops/backup.py backup

# Check the copy on Drive against the SSD and restore it into a temporary folder.
# make restore-test FULL=1 also downloads the 33 GB models folder
restore-test:
	uv run python ops/backup.py restore-test $(if $(FULL),--full)

# Copy new files from the Drive inbox (Colab results) to data/inbox. Never overwrites
pull-inbox:
	uv run python ops/backup.py pull-inbox

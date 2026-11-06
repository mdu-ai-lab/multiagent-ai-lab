# Unit tests for ops/backup.py. They test the safety parts without rclone, Drive or Docker.

import importlib.util
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from mrag.config import PROJECT_ROOT

# ops/ is a tools folder, not a package, so the script is loaded from its file path
spec = importlib.util.spec_from_file_location("backup", PROJECT_ROOT / "ops" / "backup.py")
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)

ROOT = "gdrive:Project/MDU Offline Project"


def test_run_stamp_format():
    assert backup.run_stamp(datetime(2026, 11, 2, 9, 5, 7)) == "2026-11-02_090507"


def test_drive_paths_stay_inside_the_root_folder():
    paths = backup.drive_paths(ROOT, "2026-11-02_090507")
    assert paths["multiagent-ai-lab"] == f"{ROOT}/multiagent-ai-lab"
    assert paths["multiagent-ai-lab-local"] == f"{ROOT}/multiagent-ai-lab-local"
    assert paths["history/multiagent-ai-lab"] == (
        f"{ROOT}/multiagent-ai-lab-backup/history/2026-11-02_090507/multiagent-ai-lab")
    assert paths["logs"] == f"{ROOT}/multiagent-ai-lab-backup/logs/2026-11-02_090507"
    # No target is the root itself, so other folders in it are never touched
    assert all(p.startswith(ROOT + "/") for p in paths.values())
    assert ROOT not in paths.values()


def test_history_is_never_inside_a_copy():
    # rclone refuses a history folder inside the folder it syncs to
    paths = backup.drive_paths(ROOT, "2026-11-02_090507")
    for name in backup.SOURCES:
        assert not paths[f"history/{name}"].startswith(paths[name] + "/")


def test_check_sources_stops_without_the_ssd(tmp_path):
    with pytest.raises(backup.BackupError, match="Is the SSD connected"):
        backup.check_sources({"x": (tmp_path / "missing", [])})


def test_check_sources_stops_on_an_incomplete_folder(tmp_path):
    (tmp_path / ".git").mkdir()
    with pytest.raises(backup.BackupError, match="pyproject.toml"):
        backup.check_sources({"x": (tmp_path, [".git", "pyproject.toml"])})


def test_check_sources_accepts_a_complete_folder(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "pyproject.toml").write_text("")
    backup.check_sources({"x": (tmp_path, [".git", "pyproject.toml"])})


def test_sync_command_keeps_links_permissions_and_history(tmp_path):
    cmd = backup.sync_command(Path("/src"), f"{ROOT}/multiagent-ai-lab-local",
                              f"{ROOT}/multiagent-ai-lab-backup/history/r/multiagent-ai-lab-local",
                              "multiagent-ai-lab-local", tmp_path / "log")
    assert cmd[:4] == ["rclone", "sync", "/src", f"{ROOT}/multiagent-ai-lab-local"]
    assert cmd[cmd.index("--backup-dir") + 1].endswith("/history/r/multiagent-ai-lab-local")
    for flag in ("--links", "-M", "--create-empty-src-dirs"):
        assert flag in cmd
    excluded = [cmd[i + 1] for i, a in enumerate(cmd) if a == "--exclude"]
    assert excluded == ["/hf-cache/token", "/hf-cache/stored_tokens", "/backup-logs/**"]


def test_repo_folder_is_copied_without_exclusions():
    assert backup.exclude_flags("multiagent-ai-lab") == []


def test_sqlite_copy_is_clean_and_leaves_the_source_unchanged(tmp_path):
    src = tmp_path / "app.db"
    con = sqlite3.connect(src)
    con.execute("CREATE TABLE t (x INTEGER)")
    con.executemany("INSERT INTO t VALUES (?)", [(1,), (2,), (3,)])
    con.commit()
    con.close()
    before = src.read_bytes()

    out = tmp_path / "copy.db"
    result = backup.sqlite_copy(f"sqlite:///{src}", out)
    assert result["status"] == "ok"
    assert src.read_bytes() == before
    con = sqlite3.connect(out)
    assert con.execute("SELECT count(*) FROM t").fetchone()[0] == 3
    con.close()


def test_sqlite_copy_skips_a_missing_database_without_creating_it(tmp_path):
    src = tmp_path / "app.db"
    result = backup.sqlite_copy(f"sqlite:///{src}", tmp_path / "copy.db")
    assert result["status"] == "skipped"
    assert not src.exists()


def test_sqlite_copy_skips_other_databases(tmp_path):
    result = backup.sqlite_copy("postgresql://host/db", tmp_path / "copy.db")
    assert result["status"] == "skipped"


def test_scan_counts_links_without_following_them(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "skip").mkdir()
    (tmp_path / "skip" / "b.txt").write_text("x")
    (tmp_path / "link.txt").symlink_to("a.txt")
    result = backup.scan(tmp_path, skip_top=("skip",))
    assert result["files"] == 2
    assert result["bytes"] == 5 + len("a.txt")


def test_safe_rmtree_refuses_other_folders(tmp_path):
    with pytest.raises(backup.BackupError):
        backup.safe_rmtree(tmp_path)
    with pytest.raises(backup.BackupError):
        backup.safe_rmtree(backup.REPO)
    with pytest.raises(backup.BackupError):
        backup.safe_rmtree(backup.REPO.parent / "multiagent-ai-lab-local")


def test_qdrant_snapshot_is_skipped_when_qdrant_is_off(tmp_path):
    result = backup.qdrant_snapshot("http://127.0.0.1:9", tmp_path / "q.snapshot")
    assert result["status"] == "skipped"
    assert not (tmp_path / "q.snapshot").exists()


def test_qdrant_image_comes_from_compose():
    assert backup.qdrant_image().startswith("qdrant/qdrant:v")


def test_qdrant_image_is_pinned_by_digest():
    # The tag names the release, the digest makes sure it is exactly that image
    image = backup.qdrant_image()
    assert re.fullmatch(r"qdrant/qdrant:v[\d.]+@sha256:[0-9a-f]{64}", image)


def test_mlflow_opens_a_real_mlflow_database(tmp_path, monkeypatch):
    from mlflow.tracking import MlflowClient

    # MLflow writes run files next to the working folder, so the test works in a temporary one
    monkeypatch.chdir(tmp_path)
    db = tmp_path / "mlflow.db"
    MlflowClient(tracking_uri=f"sqlite:///{db}").create_experiment("qa")
    # The Default experiment plus qa
    assert backup.mlflow_opens(db) == {"status": "ok", "experiments": 2}


def test_mlflow_opens_reports_a_broken_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    broken = tmp_path / "mlflow.db"
    broken.write_text("not a database")
    assert backup.mlflow_opens(broken)["status"] == "failed"

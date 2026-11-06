# Backup of the whole project on the SSD to Google Drive with rclone, a restore test
# and the Colab inbox. Run it through make: make backup, make restore-test, make pull-inbox.
#
# Everything goes one way, from the SSD to Drive. Nothing on Drive is deleted: a file
# that changes or disappears on the SSD is moved into a dated history folder on Drive.
# Drive layout (inside DRIVE_ROOT):
#   multiagent-ai-lab/           exact copy of the repo folder
#   multiagent-ai-lab-local/     exact copy of the folder with models and tools
#   multiagent-ai-lab-backup/    history/<run>/, logs/<run>/, snapshots/, inbox/

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Self

import yaml

from mrag.config import PROJECT_ROOT, get_settings

DRIVE_ROOT = "gdrive:Project/MDU Offline Project"
EXTRA = f"{DRIVE_ROOT}/multiagent-ai-lab-backup"

REPO = PROJECT_ROOT
LOCAL = REPO.parent / "multiagent-ai-lab-local"

# Folder name on Drive -> (folder on the SSD, paths that must exist in it).
# The marker check stops a run when the SSD is missing or a folder is empty,
# so an empty folder can never replace the copy on Drive.
SOURCES = {
    "multiagent-ai-lab": (REPO, [".git", "pyproject.toml", "src/mrag"]),
    "multiagent-ai-lab-local": (LOCAL, ["hf-cache", "models", "tools"]),
}

# Never copied. Login tokens stay out of Drive. Every backup log is already in
# multiagent-ai-lab-backup/logs/, so the local copies are not copied a second time.
EXCLUDES = {
    "multiagent-ai-lab": [],
    "multiagent-ai-lab-local": ["/hf-cache/token", "/hf-cache/stored_tokens", "/backup-logs/**"],
}

LOG_DIR = LOCAL / "backup-logs"
QDRANT_FILE = "qdrant-full.snapshot"
DB_FILE = "app.db"
MLFLOW_FILE = "mlflow.db"
MLFLOW_DB = REPO / "mlflow" / MLFLOW_FILE
RESTORE_PREFIX = ".restore-test-"
RESTORE_CONTAINER = "mrag-restore-test"
RESTORE_PORT = 6334

# --links keeps symbolic links as links, -M keeps file permissions (for example the
# executable mark of llama-server), --create-empty-src-dirs keeps empty folders.
# Larger upload pieces make big model files faster.
COPY_FLAGS = ["--links", "-M", "--create-empty-src-dirs", "--drive-chunk-size", "64M"]


class BackupError(Exception):
    pass


def run_stamp(now: datetime) -> str:
    return now.strftime("%Y-%m-%d_%H%M%S")


def drive_paths(root: str, stamp: str) -> dict[str, str]:
    extra = f"{root}/multiagent-ai-lab-backup"
    paths = {name: f"{root}/{name}" for name in SOURCES}
    paths.update({f"history/{name}": f"{extra}/history/{stamp}/{name}" for name in SOURCES})
    paths["snapshots"] = f"{extra}/snapshots"
    paths["history/snapshots"] = f"{extra}/history/{stamp}/snapshots"
    paths["logs"] = f"{extra}/logs/{stamp}"
    paths["inbox"] = f"{extra}/inbox"
    # Every target must be a sub folder of the root. Writing to the root itself
    # could touch other folders that live there
    for path in paths.values():
        if not path.startswith(root + "/"):
            raise BackupError(f"Target {path} is outside {root}")
    return paths


def check_sources(sources: dict[str, tuple[Path, list[str]]]) -> None:
    for folder, markers in sources.values():
        if not folder.is_dir():
            raise BackupError(f"{folder} not found. Is the SSD connected?")
        missing = [m for m in markers if not (folder / m).exists()]
        if missing:
            raise BackupError(f"{folder} looks incomplete, missing: {', '.join(missing)}")


def exclude_flags(name: str) -> list[str]:
    flags = []
    for pattern in EXCLUDES[name]:
        flags += ["--exclude", pattern]
    return flags


def sync_command(src: Path, dst: str, history: str, name: str, log_file: Path) -> list[str]:
    return ["rclone", "sync", str(src), dst, "--backup-dir", history,
            *COPY_FLAGS, *exclude_flags(name),
            "--log-file", str(log_file), "--log-level", "INFO"]


def rclone(args: list[str], log_file: Path | None = None) -> int:
    cmd = ["rclone", *args]
    if log_file:
        cmd += ["--log-file", str(log_file), "--log-level", "INFO"]
    return run(cmd)


def run(cmd: list[str]) -> int:
    # Show live progress when a person watches the terminal
    if cmd[0] == "rclone" and sys.stdout.isatty() and cmd[1] in ("sync", "copy", "check"):
        cmd = [*cmd, "--progress"]
    return subprocess.run(cmd, check=False).returncode


def output(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def git_info(repo: Path) -> dict:
    return {
        "commit": output(["git", "-C", str(repo), "rev-parse", "HEAD"]),
        "branch": output(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"]),
        "uncommitted_changes": bool(output(["git", "-C", str(repo), "status", "--porcelain"])),
    }


def scan(folder: Path, skip_top: tuple[str, ...] = ()) -> dict:
    # Count files and bytes the way rclone sees them: links are not followed
    files = size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        if Path(dirpath) == folder:
            dirnames[:] = [d for d in dirnames if d not in skip_top]
        for f in filenames:
            files += 1
            size += os.lstat(os.path.join(dirpath, f)).st_size
    return {"path": str(folder), "files": files, "bytes": size}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def http_json(url: str, method: str = "GET", timeout: float = 600) -> dict:
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def qdrant_reachable(url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/healthz", timeout=3):
            return True
    except (urllib.error.URLError, OSError):
        return False


def qdrant_snapshot(url: str, out_file: Path) -> dict:
    # A full snapshot holds every collection. Qdrant writes it inside its container,
    # we download it and then delete it there, so it does not use space twice
    if not qdrant_reachable(url):
        return {"status": "skipped", "reason": f"Qdrant not reachable at {url}"}
    info = http_json(f"{url}/snapshots", method="POST")["result"]
    name = info["name"]
    try:
        with urllib.request.urlopen(f"{url}/snapshots/{name}", timeout=600) as resp, \
                open(out_file, "wb") as fh:
            shutil.copyfileobj(resp, fh)
    finally:
        http_json(f"{url}/snapshots/{name}", method="DELETE")
    digest = sha256_file(out_file)
    if info.get("checksum") and info["checksum"] != digest:
        raise BackupError(f"Qdrant snapshot checksum differs: {info['checksum']} vs {digest}")
    out_file.with_name(out_file.name + ".sha256").write_text(f"{digest}  {out_file.name}\n")
    return {"status": "ok", "name": name, "bytes": out_file.stat().st_size, "sha256": digest}


def sqlite_path(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    return Path(database_url[len(prefix):]) if database_url.startswith(prefix) else None


def integrity_ok(db_file: Path) -> bool:
    con = sqlite3.connect(f"{db_file.resolve().as_uri()}?mode=ro", uri=True)
    try:
        return con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        con.close()


def sqlite_copy(database_url: str, out_file: Path) -> dict:
    # SQLite's own backup function gives a clean copy even while the app writes.
    # The source is opened read-only, so it is never changed or created
    src_path = sqlite_path(database_url)
    if src_path is None:
        return {"status": "skipped", "reason": "database is not SQLite"}
    if not src_path.exists():
        return {"status": "skipped", "reason": f"{src_path} does not exist yet"}
    src = sqlite3.connect(f"{src_path.resolve().as_uri()}?mode=ro", uri=True)
    dst = sqlite3.connect(out_file)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    if not integrity_ok(out_file):
        raise BackupError(f"SQLite copy of {src_path} failed the integrity check")
    return {"status": "ok", "source": str(src_path), "bytes": out_file.stat().st_size}


def mlflow_opens(db_file: Path) -> dict:
    # Opens a copy of the MLflow database the way the server does and lists its
    # experiments. Only used on restored copies, because MLflow may update the tables
    from mlflow.tracking import MlflowClient

    try:
        experiments = MlflowClient(tracking_uri=f"sqlite:///{db_file.resolve()}").search_experiments()
    except Exception as err:  # MLflow raises several error types for a broken database
        return {"status": "failed", "reason": str(err)}
    return {"status": "ok", "experiments": len(experiments)}


def drive_usage() -> dict:
    remote = DRIVE_ROOT.split(":")[0] + ":"
    return json.loads(output(["rclone", "about", remote, "--json"]))


def rclone_version() -> str:
    return output(["rclone", "version"]).splitlines()[0]


class RunLock:
    # Only one backup or restore test at a time. The lock is released by the
    # operating system when the process ends, even after a crash
    def __init__(self) -> None:
        self.path = Path(tempfile.gettempdir()) / "multiagent-ai-lab-backup.lock"

    def __enter__(self) -> Self:
        self.fh = open(self.path, "w")
        try:
            fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise BackupError("Another backup or restore test is running") from None
        return self

    def __exit__(self, *exc: object) -> None:
        fcntl.flock(self.fh, fcntl.LOCK_UN)
        self.fh.close()


def save_logs(stage_logs: Path, drive_target: str, local_name: str) -> int:
    # Logs go to Drive and a copy stays on the SSD in multiagent-ai-lab-local/backup-logs/
    code = rclone(["copy", str(stage_logs), drive_target])
    shutil.copytree(stage_logs, LOG_DIR / local_name)
    return code


def backup() -> int:
    started = time.time()
    stamp = run_stamp(datetime.now())
    paths = drive_paths(DRIVE_ROOT, stamp)
    check_sources(SOURCES)
    settings = get_settings()
    stage = Path(tempfile.mkdtemp(prefix="mrag-backup-"))
    logs = stage / "logs"
    snaps = stage / "snapshots"
    logs.mkdir()
    snaps.mkdir()
    manifest: dict = {
        "run": stamp,
        "started": datetime.now().isoformat(timespec="seconds"),
        "drive_root": DRIVE_ROOT,
        "rclone": rclone_version(),
        "git": git_info(REPO),
        "sources": {},
        "errors": [],
    }
    try:
        print(f"Backup {stamp} to {DRIVE_ROOT}")
        print("Qdrant snapshot ...")
        try:
            manifest["qdrant"] = qdrant_snapshot(settings.qdrant_url, snaps / QDRANT_FILE)
        except (BackupError, urllib.error.URLError, OSError, KeyError, ValueError) as err:
            manifest["qdrant"] = {"status": "failed", "reason": str(err)}
            manifest["errors"].append(f"qdrant: {err}")
        print("SQLite copy ...")
        try:
            manifest["sqlite"] = sqlite_copy(settings.database_url, snaps / DB_FILE)
        except (BackupError, sqlite3.Error) as err:
            manifest["sqlite"] = {"status": "failed", "reason": str(err)}
            manifest["errors"].append(f"sqlite: {err}")
        print("MLflow copy ...")
        try:
            manifest["mlflow"] = sqlite_copy(f"sqlite:///{MLFLOW_DB}", snaps / MLFLOW_FILE)
        except (BackupError, sqlite3.Error) as err:
            manifest["mlflow"] = {"status": "failed", "reason": str(err)}
            manifest["errors"].append(f"mlflow: {err}")

        for name, (folder, _) in SOURCES.items():
            print(f"Copying {folder} ...")
            skip = ("backup-logs",) if name == "multiagent-ai-lab-local" else ()
            entry = scan(folder, skip)
            code = run(sync_command(folder, paths[name], paths[f"history/{name}"], name,
                                    logs / f"rclone-{name}.log"))
            entry["rclone_exit"] = code
            manifest["sources"][name] = entry
            if code != 0:
                manifest["errors"].append(f"{name}: rclone exit code {code}")

        # copy (not sync): when Qdrant was skipped the last good snapshot stays on Drive.
        # An overwritten snapshot moves to the history folder
        if any(snaps.iterdir()):
            print("Copying snapshots ...")
            code = rclone(["copy", str(snaps), paths["snapshots"],
                           "--backup-dir", paths["history/snapshots"], *COPY_FLAGS],
                          logs / "rclone-snapshots.log")
            if code != 0:
                manifest["errors"].append(f"snapshots: rclone exit code {code}")
        rclone(["mkdir", paths["inbox"]])

        try:
            manifest["drive_usage"] = drive_usage()
        except subprocess.CalledProcessError as err:
            manifest["errors"].append(f"drive usage: {err}")
    finally:
        manifest["finished"] = datetime.now().isoformat(timespec="seconds")
        manifest["duration_s"] = round(time.time() - started)
        manifest["result"] = "FAILED" if manifest["errors"] else "OK"
        (logs / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        try:
            if save_logs(logs, paths["logs"], stamp) != 0:
                manifest["result"] = "FAILED"
                print("Could not upload the logs to Drive")
        finally:
            shutil.rmtree(stage)

    print_summary(manifest)
    return 0 if manifest["result"] == "OK" else 1


def print_summary(manifest: dict) -> None:
    print()
    print(f"Backup {manifest['run']}: {manifest['result']} in {manifest['duration_s']} s")
    for name, entry in manifest["sources"].items():
        print(f"  {name}: {entry['files']} files, {entry['bytes'] / 1e9:.2f} GB")
    print(f"  Qdrant snapshot: {manifest['qdrant']['status'].upper()}")
    print(f"  SQLite copy: {manifest['sqlite']['status'].upper()}")
    print(f"  MLflow copy: {manifest['mlflow']['status'].upper()}")
    for err in manifest["errors"]:
        print(f"  ERROR {err}")
    print(f"  Log: {LOG_DIR / manifest['run']}")


def safe_rmtree(path: Path) -> None:
    # Only ever deletes the temporary restore folder this script created
    if path.parent != REPO.parent or not path.name.startswith(RESTORE_PREFIX):
        raise BackupError(f"Refusing to delete {path}")
    shutil.rmtree(path)


def qdrant_image() -> str:
    compose = yaml.safe_load((REPO / "compose.yaml").read_text())
    return compose["services"]["qdrant"]["image"]


def collection_counts(url: str) -> dict[str, int]:
    names = [c["name"] for c in http_json(f"{url}/collections")["result"]["collections"]]
    return {n: http_json(f"{url}/collections/{n}")["result"]["points_count"] for n in names}


def restore_qdrant(snapshot_dir: Path, live_url: str) -> dict:
    # Starts a temporary Qdrant from the snapshot on another port and compares
    # collections and point counts with the live Qdrant
    if shutil.which("docker") is None or subprocess.run(
            ["docker", "info"], capture_output=True, check=False).returncode != 0:
        return {"status": "skipped", "reason": "Docker is not running"}
    url = f"http://127.0.0.1:{RESTORE_PORT}"
    # A container left over from an interrupted test would block the name
    subprocess.run(["docker", "rm", "-f", RESTORE_CONTAINER], capture_output=True, check=False)
    started = subprocess.run(
        ["docker", "run", "-d", "--rm", "--name", RESTORE_CONTAINER,
         "-p", f"127.0.0.1:{RESTORE_PORT}:6333", "-e", "QDRANT__TELEMETRY_DISABLED=true",
         "-v", f"{snapshot_dir}:/restore:ro", qdrant_image(),
         "./qdrant", "--storage-snapshot", f"/restore/{QDRANT_FILE}"],
        capture_output=True, text=True, check=False)
    if started.returncode != 0:
        return {"status": "failed", "reason": started.stderr.strip()}
    try:
        for _ in range(60):
            if qdrant_reachable(url):
                break
            time.sleep(1)
        else:
            return {"status": "failed", "reason": "restored Qdrant did not start"}
        restored = collection_counts(url)
        result: dict[str, object] = {"restored": restored}
        if qdrant_reachable(live_url):
            live = collection_counts(live_url)
            result["live"] = live
            result["status"] = "ok" if live == restored else "different"
        else:
            result["status"] = "ok"
            result["note"] = "live Qdrant not running, restored collections listed only"
        return result
    finally:
        subprocess.run(["docker", "stop", RESTORE_CONTAINER], capture_output=True, check=False)


def restore_test(full: bool) -> int:
    started = time.time()
    stamp = run_stamp(datetime.now())
    paths = drive_paths(DRIVE_ROOT, stamp)
    check_sources(SOURCES)
    settings = get_settings()
    temp = REPO.parent / f"{RESTORE_PREFIX}{stamp}"
    temp.mkdir()
    stage = Path(tempfile.mkdtemp(prefix="mrag-restore-"))
    logs = stage / "logs"
    logs.mkdir()
    report: dict = {"run": stamp, "full": full, "checks": {}, "errors": []}
    checks = report["checks"]

    def record(key: str, ok: bool | None, detail: object = None) -> None:
        # ok None means the check could not run (for example Docker is off)
        checks[key] = {"ok": ok, "detail": detail}
        print(f"  {'SKIP' if ok is None else 'OK  ' if ok else 'FAIL'} {key}")
        if ok is False:
            report["errors"].append(key)

    try:
        print(f"Restore test {stamp} {'(full)' if full else ''}")
        # 1. Checksum of every file on Drive against the SSD, without downloading
        for name, (folder, _) in SOURCES.items():
            code = rclone(["check", str(folder), paths[name], "--links", *exclude_flags(name)],
                          logs / f"check-drive-{name}.log")
            record(f"drive copy of {name} matches the SSD", code == 0)

        # 2. Download into a temporary folder and compare with the SSD
        names = list(SOURCES) if full else ["multiagent-ai-lab"]
        for name in names:
            folder = SOURCES[name][0]
            target = temp / name
            code = rclone(["copy", paths[name], str(target), *COPY_FLAGS],
                          logs / f"restore-{name}.log")
            if code == 0:
                code = rclone(["check", str(folder), str(target), "--links", *exclude_flags(name)],
                              logs / f"check-restored-{name}.log")
            record(f"restored {name} matches the SSD", code == 0)

        # 3. Snapshots: Qdrant checksum and a real Qdrant start, SQLite integrity
        snaps = temp / "snapshots"
        code = rclone(["copy", paths["snapshots"], str(snaps), *COPY_FLAGS],
                      logs / "restore-snapshots.log")
        qfile = snaps / QDRANT_FILE
        if code == 0 and qfile.exists():
            expected = (snaps / (QDRANT_FILE + ".sha256")).read_text().split()[0]
            record("Qdrant snapshot checksum", sha256_file(qfile) == expected)
            result = restore_qdrant(snaps, settings.qdrant_url)
            ok = None if result["status"] == "skipped" else result["status"] == "ok"
            record("Qdrant starts from the snapshot", ok, result)
        else:
            record("Qdrant snapshot on Drive", False, "not found")
        dbfile = snaps / DB_FILE
        if dbfile.exists():
            record("SQLite copy integrity", integrity_ok(dbfile))
        restored_db = temp / "multiagent-ai-lab" / "data" / DB_FILE
        if restored_db.exists():
            record("restored data/app.db integrity", integrity_ok(restored_db))
        mlflow_copy = snaps / MLFLOW_FILE
        if mlflow_copy.exists():
            record("MLflow copy integrity", integrity_ok(mlflow_copy))
            result = mlflow_opens(mlflow_copy)
            record("MLflow opens the copy", result["status"] == "ok", result)
        restored_mlflow = temp / "multiagent-ai-lab" / "mlflow" / MLFLOW_FILE
        if restored_mlflow.exists():
            record("restored mlflow/mlflow.db integrity", integrity_ok(restored_mlflow))

        # 4. Drive usage and the size of each backup folder on Drive
        report["drive_usage"] = drive_usage()
        report["drive_sizes"] = {
            name: json.loads(output(["rclone", "size", path, "--json"]))
            for name, path in [(n, paths[n]) for n in SOURCES] + [("multiagent-ai-lab-backup", EXTRA)]
        }
    finally:
        report["duration_s"] = round(time.time() - started)
        report["result"] = "FAILED" if report["errors"] else "OK"
        (logs / "restore-test.json").write_text(json.dumps(report, indent=2) + "\n")
        try:
            if save_logs(logs, f"{EXTRA}/logs/{stamp}-restore-test", f"{stamp}-restore-test"):
                print("Could not upload the logs to Drive")
        finally:
            shutil.rmtree(stage)
            safe_rmtree(temp)

    used = report.get("drive_usage", {}).get("used", 0)
    print(f"\nRestore test {stamp}: {report['result']} in {report['duration_s']} s")
    print(f"  Drive used: {used / 2**30:.1f} GiB")
    print(f"  Log: {LOG_DIR / (stamp + '-restore-test')}")
    return 0 if report["result"] == "OK" else 1


def pull_inbox() -> int:
    # Copies only files that do not exist on the SSD yet. Never overwrites
    target = REPO / "data" / "inbox"
    target.mkdir(parents=True, exist_ok=True)
    before = {p for p in target.rglob("*") if p.is_file()}
    code = rclone(["copy", f"{EXTRA}/inbox", str(target), "--ignore-existing"])
    new = sorted(p for p in target.rglob("*") if p.is_file() and p not in before)
    for p in new:
        print(f"  new: {p.relative_to(target)}")
    print(f"{len(new)} new files in {target}")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="Project backup to Google Drive")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("backup")
    test = sub.add_parser("restore-test")
    test.add_argument("--full", action="store_true", help="also download the 33 GB models folder")
    sub.add_parser("pull-inbox")
    args = parser.parse_args()
    try:
        with RunLock():
            if args.command == "backup":
                return backup()
            if args.command == "restore-test":
                return restore_test(args.full)
            return pull_inbox()
    except BackupError as err:
        print(f"Stopped: {err}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

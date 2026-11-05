# Start the local MLflow tracking server. It runs from its own locked environment in
# ops/mlflow-server, so the full mlflow package never mixes with the mlflow-skinny client
# of the platform. Address and port come from MRAG_MLFLOW_TRACKING_URI.

import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from mrag.config import PROJECT_ROOT, get_settings

SERVER_PROJECT = PROJECT_ROOT / "ops" / "mlflow-server"
DATA_DIR = PROJECT_ROOT / "mlflow"
LOCAL_HOSTS = {"127.0.0.1", "localhost"}


class MlflowServerError(Exception):
    pass


def host_and_port(tracking_uri: str) -> tuple[str, int]:
    # Only an address on this Mac is allowed, so the server is never reachable from outside
    parts = urlsplit(tracking_uri)
    if parts.scheme != "http" or parts.hostname not in LOCAL_HOSTS or parts.port is None:
        raise MlflowServerError(
            f"MRAG_MLFLOW_TRACKING_URI must be http://127.0.0.1:<port>, got {tracking_uri!r}")
    return parts.hostname, parts.port


def server_command(host: str, port: int, data_dir: Path) -> list[str]:
    # --artifacts-destination makes runs store mlflow-artifacts:/ links instead of
    # disk paths, so the mlflow folder can move to another computer
    return ["uv", "run", "--project", str(SERVER_PROJECT), "mlflow", "server",
            "--host", host, "--port", str(port),
            "--backend-store-uri", f"sqlite:///{data_dir / 'mlflow.db'}",
            "--artifacts-destination", str(data_dir / "artifacts")]


def server_env(base: dict[str, str]) -> dict[str, str]:
    env = dict(base)
    # The activated platform .venv must not be used for the server environment
    env.pop("VIRTUAL_ENV", None)
    # No usage statistics are sent to the MLflow developers
    env["MLFLOW_DISABLE_TELEMETRY"] = "true"
    return env


def main() -> int:
    try:
        host, port = host_and_port(get_settings().mlflow_tracking_uri)
    except MlflowServerError as err:
        print(err, file=sys.stderr)
        return 1
    (DATA_DIR / "artifacts").mkdir(parents=True, exist_ok=True)
    print(f"MLflow server on http://{host}:{port} (stop with Ctrl+C)", flush=True)
    cmd = server_command(host, port, DATA_DIR)
    # Replace this process with the server, so Ctrl+C stops the server directly
    os.execvpe(cmd[0], cmd, server_env(dict(os.environ)))


if __name__ == "__main__":
    sys.exit(main())

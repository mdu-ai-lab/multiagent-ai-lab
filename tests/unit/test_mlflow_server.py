# Unit tests for ops/mlflow_server.py. They check the server command without starting MLflow.

import importlib.util

import pytest

from mrag.config import PROJECT_ROOT

# ops/ is a tools folder, not a package, so the script is loaded from its file path
spec = importlib.util.spec_from_file_location("mlflow_server", PROJECT_ROOT / "ops" / "mlflow_server.py")
mlflow_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mlflow_server)


def test_host_and_port_from_the_tracking_address():
    assert mlflow_server.host_and_port("http://127.0.0.1:5001") == ("127.0.0.1", 5001)


@pytest.mark.parametrize("uri", ["http://0.0.0.0:5001", "http://192.168.1.10:5001",
                                 "https://127.0.0.1:5001", "http://127.0.0.1"])
def test_only_a_local_http_address_with_a_port_is_accepted(uri):
    with pytest.raises(mlflow_server.MlflowServerError):
        mlflow_server.host_and_port(uri)


def test_server_command_uses_the_server_environment_and_the_data_folder(tmp_path):
    cmd = mlflow_server.server_command("127.0.0.1", 5001, tmp_path)
    assert cmd[:4] == ["uv", "run", "--project", str(mlflow_server.SERVER_PROJECT)]
    assert cmd[cmd.index("--host") + 1] == "127.0.0.1"
    assert cmd[cmd.index("--port") + 1] == "5001"
    assert cmd[cmd.index("--backend-store-uri") + 1] == f"sqlite:///{tmp_path / 'mlflow.db'}"
    assert cmd[cmd.index("--artifacts-destination") + 1] == str(tmp_path / "artifacts")


def test_server_env_turns_off_telemetry_and_drops_the_platform_venv():
    base = {"PATH": "/usr/bin", "VIRTUAL_ENV": "/repo/.venv"}
    env = mlflow_server.server_env(base)
    assert env["MLFLOW_DISABLE_TELEMETRY"] == "true"
    assert "VIRTUAL_ENV" not in env
    assert env["PATH"] == "/usr/bin"
    # The caller's settings are not changed
    assert base["VIRTUAL_ENV"] == "/repo/.venv"

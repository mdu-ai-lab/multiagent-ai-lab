# Unit tests for the files of the demo Space (ops/space_files.py), its Space card and the
# upload workflow. The folder is built in a temporary place.

import importlib.util
import re

import yaml

from mrag.config import PROJECT_ROOT

# ops/ is a tools folder, not a package, so the script is loaded from its file path
spec = importlib.util.spec_from_file_location(
    "space_files", PROJECT_ROOT / "ops" / "space_files.py"
)
space_files = importlib.util.module_from_spec(spec)
spec.loader.exec_module(space_files)

LOCK = (PROJECT_ROOT / "uv.lock").read_text()


def locked(name):
    return re.search(rf'^name = "{name}"\nversion = "([^"]+)"', LOCK, re.MULTILINE)[1]


def card():
    text = (PROJECT_ROOT / "demo" / "README.md").read_text()
    return yaml.safe_load(text.split("---\n")[1])


def test_the_space_gets_exactly_the_listed_files(tmp_path):
    folder = tmp_path / "space"
    files = {str(path.relative_to(folder)) for path in space_files.build(folder)}
    platform = {
        str(path.relative_to(PROJECT_ROOT))
        for path in (PROJECT_ROOT / "src" / "mrag").rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    prompts = {
        str(path.relative_to(PROJECT_ROOT))
        for path in (PROJECT_ROOT / "configs" / "prompts").iterdir()
        if path.is_file()
    }
    listed = {"app.py", "chat.py", "README.md", "configs/models.yaml", "configs/harness.yaml"}
    assert files == listed | platform | prompts | {"requirements.txt"}
    assert not any(
        part in {"data", "tests", ".env", "__pycache__"} for f in files for part in f.split("/")
    )


def test_the_requirements_are_the_locked_versions_without_dev_tools(tmp_path):
    space_files.build(tmp_path / "space")
    pins = dict(
        line.split("==", 1)
        for line in (tmp_path / "space" / "requirements.txt").read_text().splitlines()
        if "==" in line and not line.startswith((" ", "#"))
    )
    assert pins["torch"].split(" ")[0] == "2.13.0"
    for name in ("gradio", "spaces", "transformers", "mlflow-skinny"):
        assert pins[name].split(" ")[0] == locked(name), name
    assert not {"pytest", "ruff", "mypy", "pip-audit"} & set(pins)


def test_the_space_card_matches_the_lock_and_the_python_version():
    data = card()
    assert data["sdk"] == "gradio"
    assert data["sdk_version"] == locked("gradio")
    python = (PROJECT_ROOT / ".python-version").read_text().strip()
    assert data["python_version"] == ".".join(python.split(".")[:2])
    assert data["app_file"] == "app.py"


def test_the_upload_runs_only_after_ci_on_main_through_the_fixed_list():
    text = (PROJECT_ROOT / ".github" / "workflows" / "demo.yml").read_text()
    workflow = yaml.safe_load(text)
    # PyYAML reads the key "on" as True
    assert workflow[True]["workflow_run"] == {
        "workflows": ["CI"],
        "types": ["completed"],
        "branches": ["main"],
    }
    condition = workflow["jobs"]["upload"]["if"]
    for check in ("vars.DEMO_SPACE != ''", "conclusion == 'success'", "event == 'push'"):
        assert check in condition
    assert "ops/space_files.py" in text and "--repo-type space" in text

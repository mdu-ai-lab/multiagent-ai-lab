# Checks the GPU notebooks for Kaggle and Colab: valid notebook files without saved outputs,
# every cell labelled with its number and type, the candidates of the right platform and
# the same uv version as CI.

import ast
import json
import re

import pytest
import yaml

from mrag.config import PROJECT_ROOT

PLATFORMS = ["kaggle", "colab"]
LABEL = re.compile(r"(?:### |# )Cell (\d+) \((Markdown|Code)\): \S")
CANDIDATES = yaml.safe_load((PROJECT_ROOT / "configs" / "gpu_candidates.yaml").read_text())
CI = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text()


def load(platform):
    return json.loads((PROJECT_ROOT / "notebooks" / f"{platform}_gpu.ipynb").read_text())


def settings(notebook):
    # The plain values the code cells assign, for example COMMIT = ""
    values = {}
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        for node in ast.parse("".join(cell["source"])).body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                try:
                    values[node.targets[0].id] = ast.literal_eval(node.value)
                except ValueError:
                    pass
    return values


@pytest.mark.parametrize("platform", PLATFORMS)
def test_every_cell_is_labelled_and_no_output_is_saved(platform):
    notebook = load(platform)
    assert notebook["nbformat"] == 4
    assert notebook["cells"]
    for number, cell in enumerate(notebook["cells"], start=1):
        source = "".join(cell["source"])
        label = LABEL.match(source)
        assert label, f"cell {number} has no label"
        assert int(label[1]) == number
        assert label[2].lower() == cell["cell_type"]
        if cell["cell_type"] == "code":
            assert cell["outputs"] == []
            assert cell["execution_count"] is None
            # Plain Python only: a shell line starting with ! would not stop on a failure
            ast.parse(source)


@pytest.mark.parametrize("platform", PLATFORMS)
def test_settings_match_the_candidates_and_ci(platform):
    values = settings(load(platform))
    # No default commit: the person running the notebook chooses it
    assert values["COMMIT"] == ""
    names = sorted(
        key for key, value in CANDIDATES["candidates"].items() if value["platform"] == platform
    )
    assert values["CANDIDATES"] == names
    assert values["CANDIDATE"] in names
    assert set(re.findall(r'version: "(\d+\.\d+\.\d+)"', CI)) == {values["UV_VERSION"]}
    assert values["REPO_URL"] == "https://github.com/mdu-ai-lab/multiagent-ai-lab.git"


def test_both_notebooks_share_the_same_steps():
    kaggle, colab = load("kaggle"), load("colab")
    assert len(kaggle["cells"]) == len(colab["cells"])
    for first, second in zip(kaggle["cells"], colab["cells"], strict=True):
        assert first["cell_type"] == second["cell_type"]
        assert LABEL.match("".join(first["source"]))[1] == LABEL.match("".join(second["source"]))[1]

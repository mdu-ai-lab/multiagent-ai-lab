# Keeps the layers apart by reading the imports of the code, without running it. The API,
# service.py and the route agents reach the model, the search and the tools only through the
# agent harness. The harness never imports them back.

import ast

from mrag.config import PROJECT_ROOT

SRC = PROJECT_ROOT / "src" / "mrag"
ROUTE_AGENTS = ["qa", "summary", "extract", "calc", "graphrag", "notebook", "study"]
# Model client creation, the search and the tools
MODEL_CLIENT = {"get_client", "OpenAIServerClient", "TransformersClient"}
SEARCH_AND_TOOLS = {"qdrant_client", "mrag.index", "mrag.embed", "mrag.web", "mrag.calc"}


def imports(path):
    # Every imported module, every name imported from a module and every attribute name used
    modules, names = set(), set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
            names.update(alias.name for alias in node.names)
            modules.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return modules, names


def outer_layer():
    files = [SRC / "service.py", SRC / "api.py"]
    return files + [SRC / f"{name}.py" for name in ROUTE_AGENTS if (SRC / f"{name}.py").exists()]


def test_the_outer_layer_never_reaches_the_model_search_or_tools_directly():
    for path in outer_layer():
        modules, names = imports(path)
        assert not names & MODEL_CLIENT, f"{path.name} creates a model client"
        assert not {
            module
            for module in modules
            if any(module == item or module.startswith(f"{item}.") for item in SEARCH_AND_TOOLS)
        }, f"{path.name} reaches the search or a tool directly"


def test_the_harness_never_imports_the_outer_layer():
    outer = {"mrag.service", "mrag.api"} | {f"mrag.{name}" for name in ROUTE_AGENTS}
    for path in sorted((SRC / "harness").glob("*.py")):
        modules, _ = imports(path)
        assert not modules & outer, f"harness/{path.name} imports {sorted(modules & outer)}"


def test_the_checks_see_a_forbidden_import(tmp_path):
    # The test above would pass on empty files too, so check that it really finds imports
    path = tmp_path / "bad.py"
    path.write_text(
        "from mrag.llm_client import get_client\nimport mrag.web\nimport mrag.service\n"
    )
    modules, names = imports(path)
    assert "get_client" in names
    assert {"mrag.web", "mrag.service"} <= modules

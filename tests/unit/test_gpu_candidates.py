# Checks configs/gpu_candidates.yaml: every candidate names a known platform and server and
# every download is pinned, so the GPU notebooks never fetch an unchecked file.

import re
import tomllib

import yaml

from mrag.config import PROJECT_ROOT

CANDIDATES = yaml.safe_load((PROJECT_ROOT / "configs" / "gpu_candidates.yaml").read_text())
SHA256 = re.compile(r"[0-9a-f]{64}")
CI = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text()
# Setuptools advisories that CI accepts for the vLLM lock (reasons in ci.yml) and the
# setuptools version that fixes each one (from the advisory data on osv.dev)
ACCEPTED_SETUPTOOLS = {
    "PYSEC-2026-3447": (83, 0, 0),
    "GHSA-h35f-9h28-mq5c": (83, 0, 0),
    "GHSA-xmj3-9gf7-h52w": (84, 1, 0),
}


def still_needed(setuptools: str | None) -> set[str]:
    # The advisories that are still open for this setuptools version. None: no setuptools
    if setuptools is None:
        return set()
    parts = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", setuptools)
    assert parts, f"unexpected setuptools version {setuptools!r}"
    version = tuple(int(part) for part in parts.groups())
    return {advisory for advisory, fixed in ACCEPTED_SETUPTOOLS.items() if version < fixed}


def test_llama_cpp_build_is_pinned():
    llama_cpp = CANDIDATES["servers"]["llama_cpp"]
    assert re.fullmatch(r"b\d+", llama_cpp["release"])
    assert llama_cpp["files"]
    for name, digest in llama_cpp["files"].items():
        assert llama_cpp["release"] in name, name
        assert SHA256.fullmatch(digest), name


def test_vllm_version_is_pinned():
    assert re.fullmatch(r"\d+\.\d+\.\d+", CANDIDATES["servers"]["vllm"]["version"])


def test_vllm_lock_matches_the_pinned_version():
    # The notebooks install vLLM from ops/vllm-server. A new version there needs the same
    # version here, so it is smoke-tested again before it is used
    version = CANDIDATES["servers"]["vllm"]["version"]
    folder = PROJECT_ROOT / "ops" / "vllm-server"
    project = tomllib.loads((folder / "pyproject.toml").read_text())
    assert project["project"]["dependencies"] == [f"vllm=={version}"]
    lock = tomllib.loads((folder / "uv.lock").read_text())
    assert {package["name"]: package["version"] for package in lock["package"]}["vllm"] == version
    python = (PROJECT_ROOT / ".python-version").read_text()
    assert (folder / ".python-version").read_text() == python


def test_ci_accepts_setuptools_advisories_only_while_they_are_open():
    # CI may ignore an advisory only on the vLLM audit line and only while the vLLM lock
    # holds a setuptools older than the version that fixes it
    lock = tomllib.loads((PROJECT_ROOT / "ops" / "vllm-server" / "uv.lock").read_text())
    setuptools = {package["name"]: package["version"] for package in lock["package"]}.get(
        "setuptools"
    )
    commands = [
        line
        for line in CI.splitlines()
        if "--ignore-vuln" in line and not line.strip().startswith("#")
    ]
    assert set(re.findall(r"--ignore-vuln (\S+)", "\n".join(commands))) == still_needed(setuptools)
    assert all("vllm-server.txt" in line for line in commands)


def test_each_setuptools_exception_ends_with_its_fix():
    assert still_needed("80.10.2") == set(ACCEPTED_SETUPTOOLS)
    assert still_needed("83.0.0") == {"GHSA-xmj3-9gf7-h52w"}
    assert still_needed("84.1.0") == set()
    assert still_needed(None) == set()


def test_every_candidate_is_pinned():
    servers = {"llama_cpp", "vllm"}
    for key, candidate in CANDIDATES["candidates"].items():
        assert candidate["platform"] in {"kaggle", "colab"}, key
        assert candidate["server"] in servers, key
        assert key.startswith(f"{candidate['platform']}-"), key
        assert re.fullmatch(r"[0-9a-f]{40}", candidate["revision"]), key
        assert candidate["settings"]["gpus"] == (2 if candidate["platform"] == "kaggle" else 1), key
        assert candidate["files"], key
        for name, digest in candidate["files"].items():
            assert SHA256.fullmatch(digest), f"{key}: {name}"


def test_each_platform_compares_both_servers_on_the_9b_model():
    # The smoke test compares vLLM and llama.cpp on the same model on each platform
    sources_9b = {"Qwen/Qwen3.5-9B", "unsloth/Qwen3.5-9B-GGUF"}
    for platform in ("kaggle", "colab"):
        servers = {
            candidate["server"]
            for candidate in CANDIDATES["candidates"].values()
            if candidate["platform"] == platform and candidate["source"] in sources_9b
        }
        assert servers == {"llama_cpp", "vllm"}, platform

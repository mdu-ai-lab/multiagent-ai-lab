# Checks configs/gpu_candidates.yaml: every candidate names a known platform and server and
# every download is pinned, so the GPU notebooks never fetch an unchecked file.

import re

import yaml

from mrag.config import PROJECT_ROOT

CANDIDATES = yaml.safe_load((PROJECT_ROOT / "configs" / "gpu_candidates.yaml").read_text())
SHA256 = re.compile(r"[0-9a-f]{64}")


def test_llama_cpp_build_is_pinned():
    llama_cpp = CANDIDATES["servers"]["llama_cpp"]
    assert re.fullmatch(r"b\d+", llama_cpp["release"])
    assert llama_cpp["files"]
    for name, digest in llama_cpp["files"].items():
        assert llama_cpp["release"] in name, name
        assert SHA256.fullmatch(digest), name


def test_vllm_version_is_pinned():
    assert re.fullmatch(r"\d+\.\d+\.\d+", CANDIDATES["servers"]["vllm"]["version"])


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

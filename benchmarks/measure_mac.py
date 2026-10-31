# Measure memory and speed of the local models on the Mac, alone and together.
# Each scenario starts llama-server directly, runs a fixed workload and records the
# results in results/p0_resources.csv. Mac only (uses vm_stat, footprint and sysctl).
# Not part of the platform package. Run from the repo root with:
#   uv run python benchmarks/measure_mac.py
# Close browsers and other large apps first, so the numbers are comparable.

import base64
import csv
import json
import re
import struct
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path

from mrag.config import PROJECT_ROOT, get_settings

RESULTS_FILE = PROJECT_ROOT / "results" / "p0_resources.csv"
FIRST_PORT = 18101
PAGE_SIZE = 16384  # Apple silicon memory page size in bytes

# Downloaded files, pinned by their Hugging Face revision
MAIN_DIR = "models--unsloth--Qwen3.5-9B-GGUF/snapshots/3885219b6810b007914f3a7950a8d1b469d598a5"
HELPER_DIR = "models--unsloth--Qwen3.5-2B-GGUF/snapshots/f6d5376be1edb4d416d56da11e5397a961aca8ae"


def main_model(ctx):
    return {"role": "chat", "hub": f"{MAIN_DIR}/Qwen3.5-9B-Q4_K_M.gguf",
            "hub_mmproj": f"{MAIN_DIR}/mmproj-F16.gguf", "args": ["--ctx-size", str(ctx)]}


def helper_model():
    return {"role": "chat", "hub": f"{HELPER_DIR}/Qwen3.5-2B-Q8_0.gguf",
            "args": ["--ctx-size", "4096"]}


def embed_model(quant, mmproj, ctx):
    model = {"role": "embed", "local": f"Qwen3-VL-Embedding-2B-{quant}.gguf",
             "args": ["--embedding", "--ctx-size", str(ctx), "--ubatch-size", str(ctx)]}
    if mmproj:
        model["local_mmproj"] = f"mmproj-Qwen3-VL-Embedding-2B-{mmproj}.gguf"
    return model


def rerank_model(quant, mmproj, ctx):
    model = {"role": "rerank", "local": f"Qwen3-VL-Reranker-2B-{quant}.gguf",
             "args": ["--rerank", "--ctx-size", str(ctx)]}
    if mmproj:
        model["local_mmproj"] = f"mmproj-Qwen3-VL-Reranker-2B-{mmproj}.gguf"
    return model


# Each scenario is a name and the models that run at the same time
SCENARIOS = [
    ("main alone, ctx 8192", [main_model(8192)]),
    ("main alone, ctx 32768", [main_model(32768)]),
    ("helper alone, ctx 4096", [helper_model()]),
    ("embedding alone, Q8_0, image F16, ctx 4096", [embed_model("Q8_0", "F16", 4096)]),
    ("reranker alone, Q8_0, image F16, ctx 8192", [rerank_model("Q8_0", "F16", 8192)]),
    ("main + embedding Q8_0 + reranker Q8_0, images Q8_0, ctx 2048/4096",
     [main_model(8192), embed_model("Q8_0", "Q8_0", 2048), rerank_model("Q8_0", "Q8_0", 4096)]),
    ("main + embedding Q4_K_M + reranker Q4_K_M, images Q8_0, ctx 2048/4096",
     [main_model(8192), embed_model("Q4_K_M", "Q8_0", 2048), rerank_model("Q4_K_M", "Q8_0", 4096)]),
    ("main + embedding Q4_K_M + reranker Q4_K_M text only, ctx 2048/4096",
     [main_model(8192), embed_model("Q4_K_M", "Q8_0", 2048), rerank_model("Q4_K_M", None, 4096)]),
]

COLUMNS = [
    "run_at", "git_commit", "llama_cpp_build", "gpu_limit_mb", "scenario", "status",
    "load_s", "peak_wired_increase_mb", "servers_total_mb", "chat_first_token_s",
    "chat_tokens_per_s", "image_chat_s", "embed_s", "rerank_s",
    "swap_used_start_mb", "swap_used_end_mb", "note",
]


def wired_mb():
    out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages wired down:\s+(\d+)", out).group(1))
    return pages * PAGE_SIZE / 1048576


def swap_used_mb():
    out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout
    return float(re.search(r"used = ([\d.]+)M", out).group(1))


def process_total_mb(pid):
    # footprint TOTAL line: dirty memory plus clean memory (the mapped model file)
    out = subprocess.run(["footprint", "-p", str(pid)], capture_output=True, text=True).stdout
    match = re.search(r"^\s*(\S+ \S+)\s+(\S+ \S+)\s+\S+ \S+\s+\d+\s+TOTAL", out, re.M)
    if not match:
        return 0.0
    return sum(to_mb(part) for part in match.groups())


def to_mb(text):
    number, unit = text.split()
    factor = {"B": 1 / 1048576, "KB": 1 / 1024, "MB": 1, "GB": 1024}[unit]
    return float(number) * factor


class WiredSampler(threading.Thread):
    # Reads wired memory twice per second and keeps the highest value
    def __init__(self):
        super().__init__(daemon=True)
        self.peak = wired_mb()
        self.running = True

    def run(self):
        while self.running:
            self.peak = max(self.peak, wired_mb())
            time.sleep(0.5)


def post(port, path, body, timeout=600):
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def wait_healthy(port, process, timeout=300):
    end = time.time() + timeout
    while time.time() < end:
        if process.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
                if r.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(1)
    return False


def test_image_png():
    # 256 x 128 picture: left half red, right half blue
    width, height = 256, 128
    row = b"\x00" + b"".join(b"\xff\x00\x00" if x < width // 2 else b"\x00\x00\xff"
                             for x in range(width))

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(row * height)) + chunk(b"IEND", b""))


IMAGE_B64 = base64.b64encode(test_image_png()).decode()
PASSAGE = ("The annual report describes revenue, costs and staff numbers for each region. "
           "Tables on later pages compare the results with the previous year. ") * 12


def run_chat(port, has_image):
    # Streamed answer without thinking: time to the first token and generation speed
    body = {"messages": [{"role": "user", "content": "Explain in about 100 words what a "
                          "search index is and why it makes search faster."}],
            "max_tokens": 160, "temperature": 0, "stream": True,
            "chat_template_kwargs": {"enable_thinking": False}}
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    start = time.time()
    first_token = None
    speed = None
    with urllib.request.urlopen(request, timeout=600) as response:
        for line in response:
            if not line.startswith(b"data: ") or line.strip() == b"data: [DONE]":
                continue
            event = json.loads(line[6:])
            delta = (event.get("choices") or [{}])[0].get("delta", {})
            if first_token is None and (delta.get("content") or delta.get("reasoning_content")):
                first_token = time.time() - start
            if "timings" in event:
                speed = event["timings"].get("predicted_per_second")
    result = {"chat_first_token_s": first_token, "chat_tokens_per_s": speed}
    if has_image:
        start = time.time()
        post(port, "/v1/chat/completions", {
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": "Which colours are in this picture?"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{IMAGE_B64}"}}]}],
            "max_tokens": 40, "temperature": 0,
            "chat_template_kwargs": {"enable_thinking": False}})
        result["image_chat_s"] = time.time() - start
    return result


def run_embed(port, has_image):
    inputs = [f"Section {i}. {PASSAGE}" for i in range(16)]
    if has_image:
        # llama-server picks a new image placeholder at every start and reports it in /props
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/props", timeout=10) as response:
            marker = json.load(response)["media_marker"]
        inputs.append({"prompt_string": f"A page image: {marker}", "multimodal_data": [IMAGE_B64]})
    start = time.time()
    post(port, "/embedding", {"content": inputs})
    return {"embed_s": time.time() - start}


def run_rerank(port, has_image):
    documents = [f"Document {i}. {PASSAGE}" for i in range(20)]
    if has_image:
        documents.append({"text": "A page image", "image": f"data:image/png;base64,{IMAGE_B64}"})
    start = time.time()
    post(port, "/v1/rerank", {"query": "How did revenue change in each region?",
                              "documents": documents})
    return {"rerank_s": time.time() - start}


WORKLOADS = {"chat": run_chat, "embed": run_embed, "rerank": run_rerank}


def model_command(model, settings, port):
    hub = settings.hf_home / "hub"
    path = hub / model["hub"] if "hub" in model else settings.models_dir / model["local"]
    command = [str(settings.llama_server), "--host", "127.0.0.1", "--port", str(port),
               "--offline", "--model", str(path), *model["args"]]
    if "hub_mmproj" in model:
        command += ["--mmproj", str(hub / model["hub_mmproj"])]
    if "local_mmproj" in model:
        command += ["--mmproj", str(settings.models_dir / model["local_mmproj"])]
    return command


def run_scenario(name, models, settings, log_dir):
    row = {"scenario": name, "status": "ok", "note": ""}
    row["swap_used_start_mb"] = round(swap_used_mb())
    sampler = WiredSampler()
    baseline = sampler.peak
    sampler.start()
    servers = []
    start = time.time()
    try:
        for index, model in enumerate(models):
            port = FIRST_PORT + index
            log = open(log_dir / f"{len(servers)}-{model['role']}-{port}.log", "w")
            process = subprocess.Popen(model_command(model, settings, port),
                                       stdout=log, stderr=subprocess.STDOUT)
            servers.append((model, port, process, log))
        for model, port, process, _ in servers:
            if not wait_healthy(port, process):
                raise RuntimeError(f"{model['role']} server did not start")
        row["load_s"] = round(time.time() - start, 1)
        for model, port, _, _ in servers:
            has_image = "hub_mmproj" in model or "local_mmproj" in model
            row.update(WORKLOADS[model["role"]](port, has_image))
        row["servers_total_mb"] = round(sum(process_total_mb(p.pid) for _, _, p, _ in servers))
    except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as error:
        row["status"] = "failed"
        row["note"] = str(error)[:200]
    finally:
        sampler.running = False
        sampler.join()
        for _, _, process, log in servers:
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
            log.close()
    if any("Insufficient Memory" in log_text(log.name) for _, _, _, log in servers):
        row["status"] = "out of memory"
    row["peak_wired_increase_mb"] = round(sampler.peak - baseline)
    row["swap_used_end_mb"] = round(swap_used_mb())
    time.sleep(5)  # let macOS release the memory before the next scenario
    return row


def log_text(path):
    return Path(path).read_text(errors="replace")


def gpu_limit_mb(llama_server):
    out = subprocess.run([str(llama_server), "--list-devices"], capture_output=True, text=True)
    match = re.search(r"MTL0: .*?\((\d+) MiB", out.stdout + out.stderr)
    return int(match.group(1)) if match else ""


def llama_build(llama_server):
    out = subprocess.run([str(llama_server), "--version"], capture_output=True, text=True)
    match = re.search(r"build (\d+)", out.stdout + out.stderr)
    return f"b{match.group(1)}" if match else ""


def git_commit():
    out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT_ROOT,
                         capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


def main():
    settings = get_settings()
    missing = [name for name in ("hf_home", "llama_server", "models_dir")
               if getattr(settings, name) is None]
    if missing:
        raise SystemExit(f"Set these in .env first: {', '.join(missing)}")
    common = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "git_commit": git_commit(), "llama_cpp_build": llama_build(settings.llama_server),
              "gpu_limit_mb": gpu_limit_mb(settings.llama_server)}
    log_dir = Path(tempfile.mkdtemp(prefix="mrag-measure-"))
    print(f"Server logs: {log_dir}")
    rows = []
    for name, models in SCENARIOS:
        print(f"Running: {name}", flush=True)
        row = {**common, **run_scenario(name, models, settings, log_dir)}
        rows.append(row)
        print(f"  {row['status']}, peak wired +{row['peak_wired_increase_mb']} MB", flush=True)
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with RESULTS_FILE.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: round(value, 2) if isinstance(value, float) else value
                             for key, value in row.items() if key in COLUMNS})
    print(f"Saved {len(rows)} rows to {RESULTS_FILE}")


if __name__ == "__main__":
    main()

# Smoke test of one GPU candidate from configs/gpu_candidates.yaml on Kaggle or Colab.
# First checks the NVIDIA driver and that the downloads fit on the disk. Then it
# downloads the pinned server build and model files (each checked against its SHA-256),
# starts the server, asks a few fixed public questions through llm_client.py and records
# one MLflow run in a database file inside the work folder. The run is also written as a
# result bundle, which ops/import_runs.py adds to the Mac's MLflow.
# Every answer is saved at once, so after a disconnect only the missing questions are asked.
# Run: uv run python ops/gpu_smoke.py --candidate kaggle-llamacpp-9b-16bit --work-dir <folder>

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import mlflow
import yaml
from mlflow.tracking import MlflowClient

from mrag import tracing
from mrag.config import PROJECT_ROOT, Settings
from mrag.llm_client import ModelRef, OpenAIServerClient

CANDIDATES_FILE = PROJECT_ROOT / "configs" / "gpu_candidates.yaml"
ROUTE = "gpu-smoke"
BUNDLE_FORMAT = "mrag-run-bundle/1"
CONTEXT_SIZE = 4096
MAX_ANSWER_TOKENS = 100
CHUNK = 8 * 1024 * 1024
# Room beyond the downloads: the unpacked llama.cpp build (1.0 GB for b11960), the small
# model files, logs and the caches of the servers
EXTRA_SPACE = 3 * 10**9

# Fixed public questions, each with the word a correct answer must contain
QUESTIONS = [
    ("What is the capital of Sweden? Answer in one short sentence.", "Stockholm"),
    ("What is 17 multiplied by 3? Answer with the number only.", "51"),
    ("What is the chemical symbol for gold? Answer in one word.", "Au"),
    ("Which planet is the largest in the solar system? Answer in one word.", "Jupiter"),
    ("Who wrote the novel Pride and Prejudice? Answer with the name only.", "Austen"),
]


class GpuSmokeError(Exception):
    pass


def load_candidate(
    name: str, path: Path = CANDIDATES_FILE
) -> tuple[dict[str, Any], dict[str, Any]]:
    data = yaml.safe_load(path.read_text())
    if name not in data["candidates"]:
        raise GpuSmokeError(
            f"unknown candidate {name!r}, choose one of {sorted(data['candidates'])}"
        )
    return data["candidates"][name], data["servers"]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, target: Path, sha256: str) -> None:
    # Keeps a correct file, resumes a partial one and refuses any file whose SHA-256 differs
    if target.exists():
        if sha256_of(target) == sha256:
            return
        target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    done = part.stat().st_size if part.exists() else 0
    request = urllib.request.Request(url, headers={"Range": f"bytes={done}-"} if done else {})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            # 206 means the server continues the partial file, anything else starts it again
            mode = "ab" if done and response.status == 206 else "wb"
            with part.open(mode) as out:
                shutil.copyfileobj(response, out, CHUNK)
    except urllib.error.HTTPError as error:
        # 416: the partial file is already complete
        if error.code != 416:
            raise GpuSmokeError(f"download failed ({error.code}): {url}") from error
    found = sha256_of(part)
    if found != sha256:
        part.unlink()
        raise GpuSmokeError(f"{target.name}: SHA-256 {found} differs from the pinned {sha256}")
    part.rename(target)


def extract(archive: Path, folder: Path) -> None:
    # The data filter refuses links and paths that would leave the target folder
    folder.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as tar:
        tar.extractall(folder, filter="data")


def hf_url(source: str, revision: str, file_name: str) -> str:
    return f"https://huggingface.co/{source}/resolve/{revision}/{file_name}"


def repo_files(source: str, revision: str) -> list[str]:
    url = f"https://huggingface.co/api/models/{source}/revision/{revision}"
    with urllib.request.urlopen(url, timeout=60) as response:
        return [item["rfilename"] for item in json.load(response)["siblings"]]


def model_folder(candidate: dict[str, Any], work: Path) -> Path:
    return work / "models" / candidate["source"].replace("/", "--") / candidate["revision"]


def llama_cpp_folder(servers: dict[str, Any], work: Path) -> Path:
    return work / "llama.cpp" / servers["llama_cpp"]["release"]


def llama_cpp_url(release: str, name: str) -> str:
    return f"https://github.com/ggml-org/llama.cpp/releases/download/{release}/{name}"


def pinned_downloads(
    candidate: dict[str, Any], servers: dict[str, Any], work: Path
) -> list[tuple[str, Path]]:
    # Address and target of every large pinned file the candidate needs
    source, revision = candidate["source"], candidate["revision"]
    folder = model_folder(candidate, work)
    downloads = [(hf_url(source, revision, name), folder / name) for name in candidate["files"]]
    if candidate["server"] == "llama_cpp":
        release = servers["llama_cpp"]["release"]
        archives = llama_cpp_folder(servers, work) / "archives"
        downloads += [
            (llama_cpp_url(release, name), archives / name)
            for name in servers["llama_cpp"]["files"]
        ]
    return downloads


def remote_size(url: str) -> int:
    # The servers report the size of a file without sending it
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            size = response.headers.get("Content-Length")
    except urllib.error.HTTPError as error:
        raise GpuSmokeError(f"file size check failed ({error.code}): {url}") from error
    if size is None:
        raise GpuSmokeError(f"no file size reported for {url}")
    return int(size)


def check_disk(downloads: list[tuple[str, Path]], folder: Path) -> int:
    # Stops before any download when the missing files would not fit. Returns the bytes needed
    needed = EXTRA_SPACE
    for url, target in downloads:
        if target.exists():
            continue
        part = target.with_name(target.name + ".part")
        needed += remote_size(url) - (part.stat().st_size if part.exists() else 0)
    free = shutil.disk_usage(folder).free
    if needed > free:
        raise GpuSmokeError(
            f"the downloads need {needed / 1e9:.1f} GB of free disk in {folder}, "
            f"only {free / 1e9:.1f} GB is free"
        )
    return needed


def check_driver(driver: str, minimum: int | None) -> None:
    # The first number of the driver version is its release, for example 580 in 580.82.07
    if minimum is None:
        return
    release = driver.split(".")[0]
    if not release.isdigit() or int(release) < minimum:
        raise GpuSmokeError(
            f"the NVIDIA driver {driver} is older than release {minimum}, which this server needs"
        )


def prepare_model(candidate: dict[str, Any], work: Path) -> Path:
    # Returns the GGUF file for llama.cpp or the model folder for vLLM
    source, revision = candidate["source"], candidate["revision"]
    folder = model_folder(candidate, work)
    for file_name, digest in candidate["files"].items():
        download(hf_url(source, revision, file_name), folder / file_name, digest)
    if candidate["server"] == "llama_cpp":
        return folder / next(iter(candidate["files"]))
    # vLLM also needs the small files of the repo (config, tokenizer, chat template). They
    # are fixed by the pinned revision, which is a commit and cannot change
    names = repo_files(source, revision)
    weights = {name for name in names if name.endswith(".safetensors")}
    for file_name in names:
        if file_name in candidate["files"] or file_name in weights or file_name == ".gitattributes":
            continue
        target = folder / file_name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(
                hf_url(source, revision, file_name), timeout=60
            ) as response:
                target.write_bytes(response.read())
    return folder


def prepare_llama_cpp(servers: dict[str, Any], work: Path) -> tuple[Path, list[Path]]:
    # Returns the llama-server program and the folders with its CUDA libraries
    release = servers["llama_cpp"]["release"]
    folder = llama_cpp_folder(servers, work)
    for name, digest in servers["llama_cpp"]["files"].items():
        archive = folder / "archives" / name
        download(llama_cpp_url(release, name), archive, digest)
        marker = folder / f".{name}.extracted"
        if not marker.exists():
            extract(archive, folder / "bin")
            marker.touch()
    binary = folder / "bin" / f"llama-{release}" / "llama-server"
    libraries = sorted({path.parent for path in (folder / "bin").rglob("*.so*")})
    return binary, libraries


def server_command(
    name: str, candidate: dict[str, Any], model: Path, program: Path, port: int
) -> list[str]:
    settings = candidate["settings"]
    common = ["--host", "127.0.0.1", "--port", str(port)]
    if candidate["server"] == "llama_cpp":
        # Every layer on the GPUs. With 2 GPUs llama.cpp splits the layers between them
        return [
            str(program), "--model", str(model), "--alias", name, *common,
            "--ctx-size", str(CONTEXT_SIZE), "--n-gpu-layers", "all", "--offline",
        ]  # fmt: skip
    command = [
        str(program), "serve", str(model), "--served-model-name", name, *common,
        "--dtype", settings["dtype"], "--tensor-parallel-size", str(settings["gpus"]),
        "--max-model-len", str(CONTEXT_SIZE),
    ]  # fmt: skip
    if "quantization" in settings:
        command += ["--quantization", settings["quantization"]]
    return command


def start_server(command: list[str], env: dict[str, str], log: Path) -> subprocess.Popen[bytes]:
    with log.open("ab") as out:
        return subprocess.Popen(command, stdout=out, stderr=subprocess.STDOUT, env=env)


def wait_until_ready(base_url: str, server: subprocess.Popen[bytes], timeout: float) -> float:
    # Returns the seconds the server needed. Fails at once if the server program stops
    start = time.perf_counter()
    while time.perf_counter() - start < timeout:
        if server.poll() is not None:
            raise GpuSmokeError(f"the server stopped with exit code {server.returncode}")
        try:
            with urllib.request.urlopen(f"{base_url.removesuffix('/v1')}/health", timeout=5):
                return time.perf_counter() - start
        except OSError:
            time.sleep(5)
    raise GpuSmokeError(f"the server was not ready after {timeout:.0f} s")


def stop_server(server: subprocess.Popen[bytes]) -> None:
    server.terminate()
    try:
        server.wait(timeout=60)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()


def is_correct(answer: str, expected: str) -> bool:
    # A whole word, so "Au" does not count inside "Australia"
    return re.search(rf"\b{re.escape(expected)}\b", answer, re.IGNORECASE) is not None


def ask(client: OpenAIServerClient, question: str, expected: str) -> dict[str, Any]:
    start = time.perf_counter()
    first: float | None = None
    pieces = []
    with tracing.request(ROUTE, {"question": question}) as totals:
        for piece in client.chat_stream(
            [{"role": "user", "content": question}], max_tokens=MAX_ANSWER_TOKENS
        ):
            if first is None:
                first = time.perf_counter()
            pieces.append(piece)
    end = time.perf_counter()
    answer = "".join(pieces)
    generating = end - first if first is not None else 0.0
    return {
        "question": question,
        "answer": answer,
        "correct": is_correct(answer, expected),
        "ttft_s": round((first or end) - start, 3),
        "output_tokens": totals.output_tokens,
        "tokens_per_s": round(totals.output_tokens / generating, 2) if generating > 0 else 0.0,
        "seconds": round(end - start, 3),
    }


def run_questions(client: OpenAIServerClient, checkpoint: Path) -> list[dict[str, Any]]:
    # Answers already in the checkpoint file are kept. Each new answer is written at once
    records = []
    if checkpoint.exists():
        records = [json.loads(line) for line in checkpoint.read_text().splitlines() if line]
    done = {record["question"] for record in records}
    with checkpoint.open("a") as out:
        for question, expected in QUESTIONS:
            if question in done:
                continue
            record = ask(client, question, expected)
            out.write(json.dumps(record) + "\n")
            out.flush()
            os.fsync(out.fileno())
            records.append(record)
    return records


def summary(records: list[dict[str, Any]]) -> dict[str, float]:
    if not records:
        raise GpuSmokeError("no answers were recorded")
    return {
        "questions": len(records),
        "correct": sum(record["correct"] for record in records),
        "ttft_s_median": statistics.median(record["ttft_s"] for record in records),
        "tokens_per_s_median": statistics.median(record["tokens_per_s"] for record in records),
        "answer_s_median": statistics.median(record["seconds"] for record in records),
    }


def gpu_info() -> dict[str, str]:
    # Names, memory and driver of the GPUs. "none" when nvidia-smi is missing
    query = ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]
    try:
        rows = subprocess.run(query, capture_output=True, text=True, check=True).stdout.strip()
        header = subprocess.run(["nvidia-smi"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {"gpu.count": "0", "gpu.names": "none", "gpu.driver": "none", "gpu.cuda": "none"}
    gpus = [line.split(", ") for line in rows.splitlines()]
    cuda = re.search(r"CUDA Version:\s*([\d.]+)", header)
    return {
        "gpu.count": str(len(gpus)),
        "gpu.names": "; ".join(f"{name} ({memory})" for name, memory, _ in gpus),
        "gpu.driver": gpus[0][2] if gpus else "none",
        "gpu.cuda": cuda.group(1) if cuda else "unknown",
    }


def package_list(vllm: Path, target: Path) -> Path:
    # The exact installed packages, as proof that the run used the locked vLLM environment
    command = ["uv", "pip", "freeze", "--python", str(vllm.parent / "python")]
    try:
        text = subprocess.run(command, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        text = f"not available: {error}\n"
    target.write_text(text)
    return target


def export_bundle(run_id: str, bundles: Path) -> Path:
    # One folder per run: bundle.json with the run's data and files/ with its result files
    client = MlflowClient()
    run = client.get_run(run_id)
    experiment = client.get_experiment(run.info.experiment_id)
    day = datetime.fromtimestamp(run.info.start_time / 1000, tz=UTC).date().isoformat()
    folder = bundles / f"{day}_{run.info.run_name}_{run_id}"
    files = folder / "files"
    files.mkdir(parents=True, exist_ok=True)
    client.download_artifacts(run_id, "", str(files))
    bundle = {
        "format": BUNDLE_FORMAT,
        "source_run_id": run_id,
        "experiment": experiment.name,
        "run_name": run.info.run_name,
        "status": run.info.status,
        "start_time": run.info.start_time,
        "end_time": run.info.end_time,
        "params": run.data.params,
        "metrics": run.data.metrics,
        "tags": {
            key: value for key, value in run.data.tags.items() if not key.startswith("mlflow.")
        },
    }
    (folder / "bundle.json").write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
    return folder


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test of one GPU candidate")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--vllm", default="vllm", help="the vllm program, for vLLM candidates")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--ready-timeout", type=float, default=1800)
    args = parser.parse_args()

    session_start = time.perf_counter()
    candidate, servers = load_candidate(args.candidate)
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    # MLflow keeps run files next to the working folder, so they stay in the work folder
    os.chdir(work)
    tracing.setup(Settings(profile="gpu", mlflow_tracking_uri=f"sqlite:///{work / 'mlflow.db'}"))

    gpus = gpu_info()
    needed = candidate["settings"]["gpus"]
    if int(gpus["gpu.count"]) < needed:
        raise GpuSmokeError(
            f"{args.candidate} needs {needed} GPUs, this machine has {gpus['gpu.count']}"
        )
    check_driver(gpus["gpu.driver"], servers[candidate["server"]].get("min_driver"))
    space = check_disk(pinned_downloads(candidate, servers, work), work)
    print(f"Disk check passed: {space / 1e9:.1f} GB needed in {work}")

    print(f"Downloading and checking the files of {args.candidate}")
    download_start = time.perf_counter()
    model = prepare_model(candidate, work)
    env = dict(os.environ)
    if candidate["server"] == "llama_cpp":
        program, libraries = prepare_llama_cpp(servers, work)
        env["LD_LIBRARY_PATH"] = os.pathsep.join(
            [*map(str, libraries), env.get("LD_LIBRARY_PATH", "")]
        )
        server_version = servers["llama_cpp"]["release"]
    else:
        # The full path, so the package list is read from the Python next to the program
        found = shutil.which(args.vllm)
        if found is None:
            raise GpuSmokeError(f"the vLLM program {args.vllm!r} was not found")
        program = Path(found)
        server_version = subprocess.run(
            [str(program), "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
        if server_version != servers["vllm"]["version"]:
            raise GpuSmokeError(
                f"vLLM {server_version!r} found, {servers['vllm']['version']} pinned"
            )
    download_s = time.perf_counter() - download_start

    log = work / f"server_{args.candidate}.log"
    command = server_command(args.candidate, candidate, model, program, args.port)
    print("Starting:", " ".join(command))
    server = start_server(command, env, log)
    try:
        base_url = f"http://127.0.0.1:{args.port}/v1"
        load_s = wait_until_ready(base_url, server, args.ready_timeout)
        print(f"Server ready after {load_s:.0f} s. Asking {len(QUESTIONS)} questions")
        client = OpenAIServerClient(base_url, {"main": ModelRef(name=args.candidate)})
        checkpoint = work / f"answers_{args.candidate}.jsonl"
        records = run_questions(client, checkpoint)
    finally:
        stop_server(server)

    session_s = time.perf_counter() - session_start
    metrics = summary(records) | {
        "download_s": round(download_s, 1),
        "load_s": round(load_s, 1),
        "session_s": round(session_s, 1),
        "gpu_hours": round(session_s * needed / 3600, 4),
    }
    params = gpus | {
        "candidate": args.candidate,
        "platform": candidate["platform"],
        "server": candidate["server"],
        "server.version": server_version,
        "model.source": f"{candidate['source']}@{candidate['revision']}",
        "model.files": ", ".join(
            f"{name}={digest[:12]}" for name, digest in sorted(candidate["files"].items())
        ),
        "settings": json.dumps(candidate["settings"], sort_keys=True),
        "context_size": str(CONTEXT_SIZE),
        "python": platform.python_version(),
    }
    tail = work / f"server_{args.candidate}_last_lines.log"
    tail.write_text("\n".join(log.read_text(errors="replace").splitlines()[-200:]) + "\n")
    files = [checkpoint, tail]
    if candidate["server"] == "vllm":
        files.append(package_list(program, work / f"packages_{args.candidate}.txt"))
    with tracing.run(ROUTE, run_name=args.candidate) as run_id:
        mlflow.log_params(params)
        tracing.log_results(metrics, files=files)
    bundle = export_bundle(run_id, work / "bundles")
    print(f"{metrics['correct']:.0f} of {metrics['questions']:.0f} answers correct")
    print(f"Result bundle: {bundle}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except GpuSmokeError as error:
        print(f"Smoke test failed: {error}", file=sys.stderr)
        sys.exit(1)

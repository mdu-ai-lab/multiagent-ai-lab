# Unit tests for ops/gpu_smoke.py. They need no GPU: a local web server stands in for
# Hugging Face and the model server. MLflow writes to a temporary database.

import hashlib
import importlib.util
import io
import json
import shutil
import socket
import sys
import tarfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from mrag import tracing
from mrag.config import PROJECT_ROOT, Settings
from mrag.llm_client import ModelRef, OpenAIServerClient

# ops/ is a tools folder, not a package, so the script is loaded from its file path
spec = importlib.util.spec_from_file_location("gpu_smoke", PROJECT_ROOT / "ops" / "gpu_smoke.py")
gpu_smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gpu_smoke)

DATA = b"model weights " * 1000
DIGEST = hashlib.sha256(DATA).hexdigest()
ANSWER = "Stockholm 51 Au Jupiter Austen"


class FakeWeb:
    # Serves DATA with support for resumed downloads and answers chat requests as a stream
    def __init__(self):
        self.ranges = []  # Range header of every file request
        self.questions = []
        web = self

        class Handler(BaseHTTPRequestHandler):
            def do_HEAD(self):
                # A file named missing.gguf does not exist on this server
                self.send_response(404 if self.path.endswith("missing.gguf") else 200)
                self.send_header("Content-Length", str(len(DATA)))
                self.end_headers()

            def do_GET(self):
                web.ranges.append(self.headers.get("Range"))
                start = int(self.headers["Range"][6:-1]) if self.headers.get("Range") else 0
                body = DATA[start:]
                self.send_response(206 if start else 200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                web.questions.append(request["messages"][0]["content"])

                def chunk(**fields):
                    return "data: " + json.dumps({
                        "id": "1", "object": "chat.completion.chunk", "created": 0,
                        "model": request["model"], **fields,
                    }) + "\n\n"  # fmt: skip

                body = (
                    chunk(choices=[{"index": 0, "delta": {"role": "assistant"}}])
                    + chunk(choices=[{"index": 0, "delta": {"content": ANSWER}}])
                    + chunk(
                        choices=[],
                        usage={"prompt_tokens": 20, "completion_tokens": 6, "total_tokens": 26},
                    )
                    + "data: [DONE]\n\n"
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()


@pytest.fixture
def web():
    fake = FakeWeb()
    yield fake
    fake.httpd.shutdown()


def test_download_checks_the_sha256(web, tmp_path):
    target = tmp_path / "model.gguf"
    gpu_smoke.download(f"{web.url}/model.gguf", target, DIGEST)
    assert target.read_bytes() == DATA
    # A correct file is kept without a new download
    gpu_smoke.download(f"{web.url}/model.gguf", target, DIGEST)
    assert web.ranges == [None]


def test_a_wrong_sha256_stops_and_leaves_no_file(web, tmp_path):
    target = tmp_path / "model.gguf"
    with pytest.raises(gpu_smoke.GpuSmokeError, match="differs from the pinned"):
        gpu_smoke.download(f"{web.url}/model.gguf", target, "0" * 64)
    assert list(tmp_path.iterdir()) == []


def test_a_partial_download_is_resumed(web, tmp_path):
    target = tmp_path / "model.gguf"
    (tmp_path / "model.gguf.part").write_bytes(DATA[:5000])
    gpu_smoke.download(f"{web.url}/model.gguf", target, DIGEST)
    assert web.ranges == ["bytes=5000-"]
    assert target.read_bytes() == DATA


def test_remote_size_reads_the_size_without_the_file(web):
    assert gpu_smoke.remote_size(f"{web.url}/model.gguf") == len(DATA)
    assert web.ranges == []
    with pytest.raises(gpu_smoke.GpuSmokeError, match=r"size check failed \(404\)"):
        gpu_smoke.remote_size(f"{web.url}/missing.gguf")


def test_disk_check_counts_only_the_missing_bytes(web, tmp_path, monkeypatch):
    (tmp_path / "done.gguf").write_bytes(DATA)
    (tmp_path / "half.gguf.part").write_bytes(DATA[:5000])
    downloads = [
        (f"{web.url}/done.gguf", tmp_path / "done.gguf"),
        (f"{web.url}/half.gguf", tmp_path / "half.gguf"),
        (f"{web.url}/new.gguf", tmp_path / "new.gguf"),
    ]
    needed = gpu_smoke.EXTRA_SPACE + (len(DATA) - 5000) + len(DATA)

    def free_space(bytes_free):
        usage = shutil.disk_usage(tmp_path)
        return lambda folder: usage._replace(free=bytes_free)

    monkeypatch.setattr(gpu_smoke.shutil, "disk_usage", free_space(needed))
    assert gpu_smoke.check_disk(downloads, tmp_path) == needed
    monkeypatch.setattr(gpu_smoke.shutil, "disk_usage", free_space(needed - 1))
    with pytest.raises(gpu_smoke.GpuSmokeError, match="is free"):
        gpu_smoke.check_disk(downloads, tmp_path)


def test_the_driver_must_be_new_enough_for_the_server():
    gpu_smoke.check_driver("580.82.07", 580)
    gpu_smoke.check_driver("570.86.15", None)
    with pytest.raises(gpu_smoke.GpuSmokeError, match="older than release 580"):
        gpu_smoke.check_driver("570.86.15", 580)
    with pytest.raises(gpu_smoke.GpuSmokeError, match="older than release 580"):
        gpu_smoke.check_driver("none", 580)


def test_pinned_downloads_follow_the_candidate(tmp_path):
    candidate, servers = gpu_smoke.load_candidate("kaggle-llamacpp-9b-16bit")
    downloads = gpu_smoke.pinned_downloads(candidate, servers, tmp_path)
    # The model file and both llama.cpp archives, each at its pinned revision or release
    assert len(downloads) == 1 + len(servers["llama_cpp"]["files"])
    assert candidate["revision"] in downloads[0][0]
    assert all(servers["llama_cpp"]["release"] in url for url, _ in downloads[1:])

    candidate, servers = gpu_smoke.load_candidate("kaggle-vllm-9b-16bit")
    downloads = gpu_smoke.pinned_downloads(candidate, servers, tmp_path)
    assert [target.name for _, target in downloads] == list(candidate["files"])
    assert servers["vllm"]["min_driver"] == 580


def test_extract_refuses_paths_outside_the_folder(tmp_path):
    archive = tmp_path / "bad.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("../outside.txt")
        info.size = 4
        tar.addfile(info, io.BytesIO(b"data"))
    with pytest.raises(tarfile.FilterError):
        gpu_smoke.extract(archive, tmp_path / "out")
    assert not (tmp_path / "outside.txt").exists()


def test_server_commands_follow_the_pinned_settings():
    model = Path("/m")
    name = "kaggle-llamacpp-9b-16bit"
    candidate, _ = gpu_smoke.load_candidate(name)
    command = gpu_smoke.server_command(name, candidate, model, Path("/bin/llama-server"), 8080)
    assert command[:3] == ["/bin/llama-server", "--model", "/m"]
    assert command[command.index("--n-gpu-layers") + 1] == "all"
    assert command[command.index("--alias") + 1] == name
    assert "--offline" in command

    name = "kaggle-vllm-9b-16bit"
    candidate, _ = gpu_smoke.load_candidate(name)
    command = gpu_smoke.server_command(name, candidate, model, Path("vllm"), 8080)
    assert command[:3] == ["vllm", "serve", "/m"]
    assert command[command.index("--tensor-parallel-size") + 1] == "2"
    assert command[command.index("--dtype") + 1] == "float16"
    assert command[command.index("--max-num-seqs") + 1] == "16"
    assert "--quantization" not in command
    assert "--kv-cache-dtype" not in command

    name = "colab-vllm-9b-8bit"
    candidate, _ = gpu_smoke.load_candidate(name)
    command = gpu_smoke.server_command(name, candidate, model, Path("vllm"), 8080)
    assert command[command.index("--quantization") + 1] == "fp8"
    assert command[command.index("--tensor-parallel-size") + 1] == "1"
    assert command[command.index("--max-num-seqs") + 1] == "16"

    name = "kaggle-vllm-27b-4bit"
    candidate, _ = gpu_smoke.load_candidate(name)
    command = gpu_smoke.server_command(name, candidate, model, Path("vllm"), 8080)
    assert command[command.index("--kv-cache-dtype") + 1] == "float16"
    assert command[command.index("--tensor-parallel-size") + 1] == "2"
    assert "--quantization" not in command


def test_unknown_candidate_is_reported():
    with pytest.raises(gpu_smoke.GpuSmokeError, match="unknown candidate"):
        gpu_smoke.load_candidate("nope")


def test_correct_answers_need_the_whole_word():
    assert gpu_smoke.is_correct("The symbol is Au.", "Au")
    assert not gpu_smoke.is_correct("Australia", "Au")
    assert gpu_smoke.is_correct("stockholm", "Stockholm")


def test_answers_resume_from_the_checkpoint(web, tmp_path):
    client = OpenAIServerClient(f"{web.url}/v1", {"main": ModelRef(name="m")}, max_retries=0)
    checkpoint = tmp_path / "answers.jsonl"
    # Two answers were saved before a disconnect
    saved = [
        {"question": question, "answer": ANSWER, "correct": True, "ttft_s": 0.1,
         "output_tokens": 6, "tokens_per_s": 60.0, "seconds": 0.2}
        for question, _ in gpu_smoke.QUESTIONS[:2]
    ]  # fmt: skip
    checkpoint.write_text("".join(json.dumps(record) + "\n" for record in saved))
    records = gpu_smoke.run_questions(client, checkpoint)
    assert web.questions == [question for question, _ in gpu_smoke.QUESTIONS[2:]]
    assert len(records) == len(gpu_smoke.QUESTIONS)
    assert all(record["correct"] for record in records)
    assert all(record["output_tokens"] == 6 for record in records)
    assert len(checkpoint.read_text().splitlines()) == len(gpu_smoke.QUESTIONS)
    metrics = gpu_smoke.summary(records)
    assert metrics["questions"] == 5
    assert metrics["correct"] == 5


def test_an_empty_answer_list_is_an_error():
    with pytest.raises(gpu_smoke.GpuSmokeError, match="no answers"):
        gpu_smoke.summary([])


# A stand-in for llama-server: answers /health and streams the same answer to every question
FAKE_SERVER = """
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        def chunk(**fields):
            event = {"id": "1", "object": "chat.completion.chunk", "created": 0,
                     "model": request["model"], **fields}
            return "data: " + json.dumps(event) + "\\n\\n"
        body = (chunk(choices=[{"index": 0, "delta": {"content": ANSWER}}])
                + chunk(choices=[], usage={"prompt_tokens": 20, "completion_tokens": 6,
                                           "total_tokens": 26})
                + "data: [DONE]\\n\\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass

HTTPServer(("127.0.0.1", int(sys.argv[sys.argv.index("--port") + 1])), Handler).serve_forever()
"""


def test_the_whole_job_writes_a_bundle(tmp_path, monkeypatch):
    program = tmp_path / "llama-server"
    program.write_text(f"#!{sys.executable}\nANSWER = {ANSWER!r}\n{FAKE_SERVER}")
    program.chmod(0o755)
    model = tmp_path / "model.gguf"
    model.write_bytes(DATA)
    # Downloads, file sizes and nvidia-smi are replaced, everything else runs for real
    monkeypatch.setattr(gpu_smoke, "prepare_model", lambda candidate, work: model)
    monkeypatch.setattr(gpu_smoke, "prepare_llama_cpp", lambda servers, work: (program, []))
    monkeypatch.setattr(gpu_smoke, "remote_size", lambda url: 1)
    gpus = {"gpu.count": "2", "gpu.names": "T4; T4", "gpu.driver": "580.82.07", "gpu.cuda": "13.0"}
    monkeypatch.setattr(gpu_smoke, "gpu_info", lambda: gpus)
    work = tmp_path / "work"
    # No --port: the server gets a free port, as on Kaggle and Colab
    monkeypatch.setattr(
        sys,
        "argv",
        ["gpu_smoke.py", "--candidate", "kaggle-llamacpp-9b-16bit", "--work-dir", str(work),
         "--ready-timeout", "60"],
    )  # fmt: skip
    monkeypatch.chdir(tmp_path)
    try:
        assert gpu_smoke.main() == 0
    finally:
        tracing.setup(Settings(profile="ci"))
    [bundle] = (work / "bundles").iterdir()
    data = json.loads((bundle / "bundle.json").read_text())
    assert data["run_name"] == "kaggle-llamacpp-9b-16bit"
    assert data["status"] == "FINISHED"
    assert data["metrics"]["correct"] == 5
    assert data["metrics"]["gpu_hours"] > 0
    assert data["params"]["server.version"] == "b11960"
    assert data["params"]["gpu.count"] == "2"
    files = sorted(path.name for path in (bundle / "files").iterdir())
    assert files == [
        "answers_kaggle-llamacpp-9b-16bit.jsonl",
        "server_kaggle-llamacpp-9b-16bit_last_lines.log",
    ]


def test_free_port_skips_a_port_in_use():
    # A port another program listens on is never chosen. The chosen port can be used at once
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        port = gpu_smoke.free_port()
        assert port != busy.getsockname()[1]
        with socket.socket() as server:
            server.bind(("127.0.0.1", port))


def test_a_server_that_stops_fails_at_once(tmp_path):
    # The error shows the end of the server log, which holds the reason
    log = tmp_path / "server.log"
    server = gpu_smoke.start_server(
        [sys.executable, "-c", "print('no GPU found'); raise SystemExit(3)"], {}, log
    )
    with pytest.raises(gpu_smoke.GpuSmokeError, match=r"exit code 3[\s\S]*no GPU found"):
        gpu_smoke.wait_until_ready("http://127.0.0.1:9/v1", server, timeout=60, log=log)


def test_gpu_profile_records_runs_in_a_database_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings(profile="gpu", mlflow_tracking_uri=f"sqlite:///{tmp_path}/mlflow.db")
    try:
        assert tracing.setup(settings) is True
        with tracing.run(gpu_smoke.ROUTE, run_name="candidate") as run_id:
            tracing.log_results({"correct": 5.0})
        bundle = gpu_smoke.export_bundle(run_id, tmp_path / "bundles")
    finally:
        tracing.setup(Settings(profile="ci"))
    data = json.loads((bundle / "bundle.json").read_text())
    assert data["format"] == gpu_smoke.BUNDLE_FORMAT
    assert data["source_run_id"] == run_id
    assert data["params"]["profile"] == "gpu"
    assert data["metrics"] == {"correct": 5.0}
    assert data["tags"]["mrag.pipeline_version"].startswith("p-")

# Unit tests for src/mrag/eval_data.py with a small web server on this computer. Nothing goes
# to the internet and no real dataset is downloaded.

import hashlib
import io
import tarfile
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from pydantic import ValidationError

from mrag import eval_data

BODY = bytes(range(256)) * 400  # 102,400 bytes
BODY_SHA = hashlib.sha256(BODY).hexdigest()
# The datasets the evaluation plan names, with the speech sets and the Swedish sets chosen for it
PLANNED = {
    "longdocurl", "qasper", "tatdqa", "cord", "govreport", "peersum", "2wikimultihopqa",
    "musique", "librispeech", "ami", "scandiqa-sv", "belebele-sv", "mkqa", "swefaq", "fleurs-sv",
}  # fmt: skip

seen = {"ranges": [], "cut": 0, "requests": 0}


def tar_bytes(name: str, data: bytes) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        info = tarfile.TarInfo(name)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def zip_bytes(name: str, data: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        bundle.writestr(name, data)
    return buffer.getvalue()


FILES = {
    "/good": BODY,
    "/no-range": BODY,
    "/cut": BODY,
    "/good.tar.gz": tar_bytes("inner/a.txt", b"hello"),
    "/evil.tar.gz": tar_bytes("../evil.txt", b"bad"),
    "/good.zip": zip_bytes("inner/b.txt", b"hello"),
    "/evil.zip": zip_bytes("../evil.txt", b"bad"),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        seen["requests"] += 1
        body = FILES.get(self.path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            return
        start = 0
        wanted = self.headers.get("Range")
        if wanted:
            seen["ranges"].append(wanted)
        if wanted and self.path != "/no-range":
            start = int(wanted.removeprefix("bytes=").removesuffix("-"))
            self.send_response(206)
        else:
            self.send_response(200)
        rest = body[start:]
        self.send_header("Content-Length", str(len(rest)))
        self.end_headers()
        if self.path == "/cut" and seen["cut"] == 0:
            # The first answer breaks off half way, as a dropped connection does
            seen["cut"] += 1
            self.wfile.write(rest[: len(rest) // 2])
            self.wfile.flush()
            self.connection.close()
            return
        self.wfile.write(rest)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    monkeypatch.setattr(eval_data, "PAUSE_S", 0)
    # Small blocks, so a cut connection leaves part of the file behind as in a real download
    monkeypatch.setattr(eval_data, "CHUNK", 4096)
    seen.update(ranges=[], cut=0, requests=0)


def item(url, path="file.bin", body=BODY, unpack=False, sha=None):
    # Built without validation, because the test server has no https address
    return eval_data.DataFile.model_construct(
        path=path,
        url=url,
        size=len(body),
        sha256=sha or hashlib.sha256(body).hexdigest(),
        hash_from="measured",
        unpack=unpack,
    )


def test_the_real_catalog_is_valid_and_lists_every_planned_dataset():
    catalog = eval_data.load_catalog()
    assert {dataset.name for dataset in catalog.datasets} == PLANNED
    for dataset in catalog.datasets:
        assert dataset.licence and dataset.licence_source.startswith("https://")
        for entry in dataset.files:
            # Hugging Face files must name a fixed 40-character revision, never a branch
            if "huggingface.co" in entry.url:
                assert "/resolve/main/" not in entry.url
                revision = entry.url.split("/resolve/")[1].split("/")[0]
                assert len(revision) == 40


def test_a_download_is_written_and_checked(server, tmp_path):
    entry = item(f"{server}/good")
    assert eval_data.download_file(entry, tmp_path) == "downloaded and verified"
    assert (tmp_path / "file.bin").read_bytes() == BODY
    assert not (tmp_path / "file.bin.part").exists()


def test_a_verified_file_is_not_downloaded_again(server, tmp_path):
    (tmp_path / "file.bin").write_bytes(BODY)
    assert eval_data.download_file(item(f"{server}/good"), tmp_path) == "already verified"
    assert seen["requests"] == 0


def test_a_part_file_continues_where_it_stopped(server, tmp_path):
    (tmp_path / "file.bin.part").write_bytes(BODY[:1000])
    eval_data.download_file(item(f"{server}/good"), tmp_path)
    assert seen["ranges"] == ["bytes=1000-"]
    assert (tmp_path / "file.bin").read_bytes() == BODY


def test_a_server_without_ranges_makes_the_file_start_again(server, tmp_path):
    (tmp_path / "file.bin.part").write_bytes(BODY[:1000])
    eval_data.download_file(item(f"{server}/no-range"), tmp_path)
    assert (tmp_path / "file.bin").read_bytes() == BODY


def test_a_cut_connection_is_tried_again_and_continues(server, tmp_path):
    eval_data.download_file(item(f"{server}/cut"), tmp_path)
    assert seen["cut"] == 1
    assert len(seen["ranges"]) == 1
    assert (tmp_path / "file.bin").read_bytes() == BODY


def test_a_wrong_hash_stops_and_deletes_the_file(server, tmp_path):
    entry = item(f"{server}/good", sha="0" * 64)
    with pytest.raises(eval_data.DataError, match="was deleted"):
        eval_data.download_file(entry, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_a_missing_file_stops_at_once(server, tmp_path):
    with pytest.raises(eval_data.DataError, match="HTTP 404"):
        eval_data.download_file(item(f"{server}/nothing"), tmp_path)
    assert seen["requests"] == 1


@pytest.mark.parametrize("name, inner", [("good.tar.gz", "a.txt"), ("good.zip", "b.txt")])
def test_archives_are_unpacked_once(server, tmp_path, name, inner):
    entry = item(f"{server}/{name}", path=name, body=FILES[f"/{name}"], unpack=True)
    eval_data.download_file(entry, tmp_path)
    assert eval_data.unpack(entry, tmp_path) == "unpacked"
    assert (tmp_path / "good" / "inner" / inner).read_bytes() == b"hello"
    assert eval_data.unpack(entry, tmp_path) == "already unpacked"


@pytest.mark.parametrize("name", ["evil.tar.gz", "evil.zip"])
def test_an_archive_path_outside_its_folder_is_refused(server, tmp_path, name):
    entry = item(f"{server}/{name}", path=name, body=FILES[f"/{name}"], unpack=True)
    eval_data.download_file(entry, tmp_path)
    with pytest.raises((eval_data.DataError, tarfile.TarError)):
        eval_data.unpack(entry, tmp_path)
    assert not (tmp_path / "evil.txt").exists()
    assert not (tmp_path / "evil").exists()


def test_verify_finds_missing_and_changed_files(tmp_path, capsys):
    good = item("https://example.org/a", path="a.bin")
    changed = item("https://example.org/b", path="b.bin")
    missing = item("https://example.org/c", path="c.bin")
    dataset = eval_data.Dataset.model_construct(
        name="demo", title="Demo", use="test", licence="x", licence_source="https://x",
        files=[good, changed, missing],
    )  # fmt: skip
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "a.bin").write_bytes(BODY)
    (tmp_path / "demo" / "b.bin").write_bytes(BODY[:-1] + b"x")
    assert eval_data.verify([dataset], tmp_path) is False
    report = capsys.readouterr().out
    assert "OK                 demo/a.bin" in report
    assert "WRONG HASH OR SIZE demo/b.bin" in report
    assert "MISSING            demo/c.bin" in report


@pytest.mark.parametrize(
    "change, message",
    [
        ({"path": "../outside.bin"}, "inside the dataset folder"),
        ({"path": "/etc/passwd"}, "inside the dataset folder"),
        ({"url": "http://example.org/a"}, "https"),
        ({"sha256": "abc"}, "String should match"),
        ({"path": "a.json", "unpack": True}, "unpack needs"),
    ],
)
def test_bad_list_entries_are_refused(change, message):
    entry = {
        "path": "a.tgz",
        "url": "https://example.org/a",
        "size": 1,
        "sha256": "0" * 64,
        "hash_from": "source",
    } | change
    with pytest.raises(ValidationError, match=message):
        eval_data.DataFile.model_validate(entry)


def test_unknown_dataset_names_are_refused():
    with pytest.raises(eval_data.DataError, match="unknown dataset: nope"):
        eval_data.load_catalog().pick(["qasper", "nope"])

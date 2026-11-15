# Unit tests for ops/health_check.py with a small web server on this computer and fake answers
# of the Hugging Face API. Nothing goes to the internet.

import importlib.util
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mrag.config import PROJECT_ROOT

# ops/ is a tools folder, not a package, so the script is loaded from its file path
spec = importlib.util.spec_from_file_location(
    "health_check", PROJECT_ROOT / "ops" / "health_check.py"
)
health_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health_check)

calls = {"flaky": 0}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        base = f"http://127.0.0.1:{self.server.server_port}"
        pages = {
            "/": (
                200,
                f'<h1>multiagent-ai-lab</h1><a href="{base}/ok">ok</a> <a href="#x">in page</a>',
            ),
            "/broken-link": (200, f'<p>multiagent-ai-lab</p><a href="{base}/missing">gone</a>'),
            "/wrong": (200, "<p>Some other site</p>"),
            "/ok": (200, "fine"),
        }
        if self.path == "/flaky":
            calls["flaky"] += 1
            status, body = (503, "busy") if calls["flaky"] == 1 else (200, "fine")
        else:
            status, body = pages.get(self.path, (404, "not found"))
        self.send_response(status)
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def site():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(autouse=True)
def no_pause(monkeypatch):
    monkeypatch.setattr(health_check, "PAUSE_S", 0)


def run(monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, "argv", ["health_check.py", *args])
    code = health_check.main()
    return code, capsys.readouterr().out


def test_a_good_dashboard_with_working_links_passes(site, monkeypatch, capsys):
    code, out = run(monkeypatch, capsys, "--dashboard", f"{site}/")
    assert code == 0
    assert out.startswith("All 2 checks passed")
    # A link inside the page itself is not an address of another site
    assert "#x" not in out


def test_a_wrong_address_fails(site, monkeypatch, capsys):
    code, out = run(monkeypatch, capsys, "--dashboard", f"{site}/", "--extra", f"{site}/nothing")
    assert code == 1
    assert f"- FAIL {site}/nothing: HTTP 404" in out


def test_a_page_without_the_dashboard_text_fails(site):
    [check] = health_check.check_dashboard(f"{site}/wrong")
    assert not check.ok and "without the text" in check.detail


def test_a_broken_link_fails_only_that_link(site):
    page, link = health_check.check_dashboard(f"{site}/broken-link")
    assert page.ok
    assert not link.ok and link.name == f"{site}/missing"


def test_a_server_error_is_tried_again(site):
    calls["flaky"] = 0
    assert health_check.check_url(f"{site}/flaky").ok
    assert calls["flaky"] == 2


def space_answer(monkeypatch, status, body):
    monkeypatch.setattr(health_check, "fetch", lambda url: (status, json.dumps(body)))


@pytest.mark.parametrize(
    ("status", "body", "ok"),
    [
        (200, {"runtime": {"stage": "RUNNING"}}, True),
        (200, {"runtime": {"stage": "SLEEPING"}}, True),
        (200, {"runtime": {"stage": "BUILD_ERROR"}}, False),
        (200, {"runtime": {"stage": "RUNTIME_ERROR"}}, False),
        (401, {}, False),
    ],
)
def test_the_space_state(monkeypatch, status, body, ok):
    space_answer(monkeypatch, status, body)
    assert health_check.check_space("owner/demo").ok is ok


def test_the_report_is_also_written_to_a_file(site, monkeypatch, capsys, tmp_path):
    report = tmp_path / "report.md"
    code, out = run(monkeypatch, capsys, "--dashboard", f"{site}/wrong", "--report", str(report))
    assert code == 1
    assert report.read_text() == out
    assert out.startswith("1 of 1 checks failed")

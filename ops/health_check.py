# Checks the live sites: the dashboard answers and shows its page, every link on it works and,
# once it exists, the demo Space is not in an error state. Prints a report and exits with 1
# when a check fails. The weekly workflow .github/workflows/health.yml turns that into an issue.
# Run: uv run python ops/health_check.py --dashboard URL [--space OWNER/NAME] [--extra URL]

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

# Text the dashboard page always shows, so an empty or wrong page fails too
DASHBOARD_TEXT = "multiagent-ai-lab"
SPACE_API = "https://huggingface.co/api/spaces/{space}"
# The error states in huggingface_hub's SpaceStage. Any other state is up, a sleeping Space too
SPACE_ERRORS = {
    "NO_APP_FILE", "CONFIG_ERROR", "BUILD_ERROR", "RUNTIME_ERROR", "DELETING", "STOPPED", "PAUSED",
}  # fmt: skip
TIMEOUT_S = 20
TRIES = 3
# A GitHub page can answer HTTP 503 for a short time, so the tries cover about one minute
PAUSE_S = 30.0
USER_AGENT = "multiagent-ai-lab-health-check"


@dataclass(frozen=True)
class Check:
    ok: bool
    name: str
    detail: str


class Links(HTMLParser):
    # Every address a page links to or loads from another site
    def __init__(self) -> None:
        super().__init__()
        self.found: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in ("href", "src") and value and value.startswith(("http://", "https://")):
                self.found.append(value)


def fetch(url: str) -> tuple[int, str]:
    # The status and the text. A server error or a network problem is tried again after a
    # short pause, so one blip is no failure. A 404 is final at once
    status, text = 0, ""
    for attempt in range(TRIES):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
                return response.status, response.read().decode(errors="replace")
        except urllib.error.HTTPError as error:
            status, text = error.code, ""
            if error.code < 500:
                return status, text
        except OSError as error:
            status, text = 0, str(error)
        if attempt < TRIES - 1:
            time.sleep(PAUSE_S)
    return status, text


def check_url(url: str) -> Check:
    status, text = fetch(url)
    if 200 <= status < 400:
        return Check(True, url, f"HTTP {status}")
    return Check(False, url, f"HTTP {status}" if status else f"no answer ({text})")


def check_dashboard(url: str) -> list[Check]:
    status, text = fetch(url)
    if status != 200:
        detail = f"HTTP {status}" if status else f"no answer ({text})"
        return [Check(False, f"dashboard {url}", detail)]
    if DASHBOARD_TEXT not in text:
        return [Check(False, f"dashboard {url}", f"HTTP 200 without the text {DASHBOARD_TEXT}")]
    links = Links()
    links.feed(text)
    checks = [Check(True, f"dashboard {url}", "HTTP 200")]
    return checks + [check_url(link) for link in sorted(set(links.found))]


def check_space(space: str) -> Check:
    name = f"demo Space {space}"
    status, text = fetch(SPACE_API.format(space=space))
    if status != 200:
        return Check(False, name, f"not found or not public (HTTP {status})")
    stage = str(json.loads(text).get("runtime", {}).get("stage", "unknown"))
    return Check(stage not in SPACE_ERRORS, name, f"state {stage}")


def report(checks: list[Check]) -> str:
    failed = sum(not check.ok for check in checks)
    lines = [f"- {'OK' if check.ok else 'FAIL'} {check.name}: {check.detail}" for check in checks]
    summary = (
        f"{failed} of {len(checks)} checks failed" if failed else f"All {len(checks)} checks passed"
    )
    return "\n".join([summary, "", *lines])


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the live dashboard and the demo Space")
    parser.add_argument("--dashboard", required=True, help="Address of the live dashboard")
    parser.add_argument("--space", default="", help="The demo Space, for example owner/name")
    parser.add_argument("--extra", default="", help="One more address to check")
    parser.add_argument("--report", type=Path, help="Also write the report to this file")
    args = parser.parse_args()
    checks = check_dashboard(args.dashboard)
    if args.space:
        checks.append(check_space(args.space))
    if args.extra:
        checks.append(check_url(args.extra))
    text = report(checks)
    print(text)
    if args.report:
        args.report.write_text(text + "\n")
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())

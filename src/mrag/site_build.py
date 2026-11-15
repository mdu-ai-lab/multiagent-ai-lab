# Builds the live dashboard: one static HTML page from docs/WORK_PLAN.md (progress per phase
# and step, the architecture diagram), CHANGELOG.md and the published result summaries in
# results/ (the newest scores with their trend). It reads only files that are public in the
# repo. The page uses no JavaScript and no files from other sites.
# Run: uv run python -m mrag.site_build

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from mrag import tracing
from mrag.config import PROJECT_ROOT

PLAN_FILE = PROJECT_ROOT / "docs" / "WORK_PLAN.md"
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"
RESULTS_DIR = PROJECT_ROOT / "results"
TEMPLATES_DIR = Path(__file__).parent / "templates" / "site"
OUT_DIR = PROJECT_ROOT / "_site"
REPO_URL = "https://github.com/mdu-ai-lab/multiagent-ai-lab"

PHASE = re.compile(r"^### (Phase \w+): (.+)$")
# A step row of the phase plan: | 1.5 Free GPU profile | ... | Done |
STEP_ROW = re.compile(r"^\| (\d+[AB]?\.\d+) ([^|]+?) \|.*\| ([^|]+?) \|$")
STATUSES = {"Done", "Not done"}
STATE_ROW = re.compile(r"^\| ([^|]+?) \| ([^|]+?) \|$")
ARCHITECTURE = re.compile(r"^### 8\.1 Architecture\n\n```\n(.*?)\n```", re.MULTILINE | re.DOTALL)


class SiteBuildError(Exception):
    pass


@dataclass(frozen=True)
class Step:
    id: str
    title: str
    done: bool


@dataclass
class Phase:
    name: str
    title: str
    steps: list[Step] = field(default_factory=list)

    @property
    def done(self) -> int:
        return sum(step.done for step in self.steps)


@dataclass
class Release:
    title: str
    sections: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class Series:
    # The published runs of one route, profile and dataset set, oldest first
    route: str
    profile: str
    datasets: str
    runs: list[dict[str, Any]]

    @property
    def latest(self) -> dict[str, Any]:
        return self.runs[-1]

    def trend(self, metric: str) -> list[float]:
        return [
            float(run["metrics"][metric])
            for run in self.runs
            if isinstance(run["metrics"].get(metric), int | float)
        ]


def read_state(plan: str) -> dict[str, str]:
    # The table of section 1, current state
    section = plan.split("\n## 1. ", 1)[-1].split("\n## 2. ", 1)[0]
    rows = [STATE_ROW.match(line) for line in section.splitlines()]
    return {row[1]: row[2] for row in rows if row and row[1] not in {"Item", "---"}}


def read_phases(plan: str) -> list[Phase]:
    # Every step row of the phase plan (section 12) ends with its status
    phases: list[Phase] = []
    for line in plan.split("\n## 12. ", 1)[-1].split("\n## 13. ", 1)[0].splitlines():
        if phase := PHASE.match(line):
            phases.append(Phase(phase[1], phase[2]))
        elif phases and (step := STEP_ROW.match(line)):
            if step[3] not in STATUSES:
                raise SiteBuildError(f"Step {step[1]} has the unknown status '{step[3]}'")
            phases[-1].steps.append(Step(step[1], step[2], step[3] == "Done"))
    if not phases or not all(phase.steps for phase in phases):
        raise SiteBuildError("The phase plan in section 12 has no steps to show")
    return phases


def read_architecture(plan: str) -> str:
    found = ARCHITECTURE.search(plan)
    if found is None:
        raise SiteBuildError("No architecture diagram in section 8.1")
    return found[1]


def read_changelog(text: str) -> list[Release]:
    # Versions (## [...]), their sections (### Added) and one item per line (- ...)
    releases: list[Release] = []
    section: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            releases.append(Release(line[3:]))
            section = None
        elif line.startswith("### ") and releases:
            section = releases[-1].sections.setdefault(line[4:], [])
        elif line.startswith("- ") and section is not None:
            section.append(line[2:])
    return releases


def read_results(results_dir: Path) -> list[Series]:
    # The files export_results.py writes: results/<route>/<date>_<run id>.json
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for path in sorted(results_dir.glob("*/*.json")):
        try:
            run = json.loads(path.read_text())
        except json.JSONDecodeError as error:
            raise SiteBuildError(f"{path.name} is not valid JSON: {error}") from error
        params = run.get("params", {})
        datasets = ", ".join(
            f"{key.removeprefix('dataset.')} {value}"
            for key, value in sorted(params.items())
            if key.startswith("dataset.")
        )
        key = (run["route"], params.get("profile", "unknown"), datasets or "none")
        groups.setdefault(key, []).append(run)
    return [
        Series(
            route, profile, datasets, sorted(runs, key=lambda run: (run["started"], run["run_id"]))
        )
        for (route, profile, datasets), runs in sorted(groups.items())
    ]


def trend_points(values: list[float], width: int = 120, height: int = 28) -> str:
    # The points of a small line chart, oldest value on the left. Empty below 2 values
    if len(values) < 2:
        return ""
    low, high = min(values), max(values)
    spread = high - low or 1.0
    step = width / (len(values) - 1)
    return " ".join(
        f"{index * step:.1f},{height - (value - low) / spread * height:.1f}"
        for index, value in enumerate(values)
    )


def render(plan: str, changelog: str, results_dir: Path) -> str:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        # Every value is HTML-escaped, so text from the docs cannot change the page
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.globals["trend_points"] = trend_points
    phases = read_phases(plan)
    steps = [step for phase in phases for step in phase.steps]
    return environment.get_template("index.html.j2").render(
        state=read_state(plan),
        phases=phases,
        done=sum(step.done for step in steps),
        total=len(steps),
        series=read_results(results_dir),
        architecture=read_architecture(plan),
        releases=read_changelog(changelog),
        commit=tracing.git_state()["git_commit"],
        built=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        repo_url=REPO_URL,
    )


def build(
    out_dir: Path = OUT_DIR,
    plan_file: Path = PLAN_FILE,
    changelog_file: Path = CHANGELOG_FILE,
    results_dir: Path = RESULTS_DIR,
) -> Path:
    page = out_dir / "index.html"
    out_dir.mkdir(parents=True, exist_ok=True)
    page.write_text(render(plan_file.read_text(), changelog_file.read_text(), results_dir))
    return page


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the live dashboard")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="Default: _site in the repo")
    try:
        page = build(parser.parse_args().out)
    except SiteBuildError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Dashboard written: {page} ({page.stat().st_size / 1000:.0f} kB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

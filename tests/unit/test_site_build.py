# Unit tests for the live dashboard generator. They read the real plan and changelog and
# write result files and pages into a temporary folder.

import json
import re

import pytest

from mrag import site_build
from mrag.config import PROJECT_ROOT

PLAN = (PROJECT_ROOT / "docs" / "WORK_PLAN.md").read_text()
CHANGELOG = (PROJECT_ROOT / "CHANGELOG.md").read_text()


def write_result(folder, route, run_id, started, metrics, profile="mac", dataset="qasper"):
    path = folder / route / f"{started[:10]}_{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    run = {
        "route": route,
        "run_id": run_id,
        "started": started,
        "params": {"profile": profile, f"dataset.{dataset}": "abc123"},
        "metrics": metrics,
        "tags": {"mrag.pipeline_version": f"p-{run_id}"},
    }
    path.write_text(json.dumps(run))


def test_the_real_plan_has_every_step_with_a_known_status():
    phases = site_build.read_phases(PLAN)
    section = PLAN.split("\n## 12. ", 1)[1].split("\n## 13. ", 1)[0]
    rows = re.findall(r"^\| \d+[AB]?\.\d+ ", section, re.MULTILINE)
    assert len(phases) == 19
    assert sum(len(phase.steps) for phase in phases) == len(rows)
    assert phases[0].name == "Phase 0" and phases[0].done == len(phases[0].steps)


def test_an_unknown_status_stops_the_build():
    plan = "## 12. Phase plan\n\n### Phase 0: Start\n\n| 0.1 Setup | a | b | c | Almost |\n"
    with pytest.raises(site_build.SiteBuildError, match="unknown status 'Almost'"):
        site_build.read_phases(plan)


def test_the_real_state_diagram_and_changelog_are_read():
    state = site_build.read_state(PLAN)
    assert {"Plan status", "Last completed step", "Latest version tag"} <= set(state)
    assert "harness.run()" in site_build.read_architecture(PLAN)
    releases = site_build.read_changelog(CHANGELOG)
    assert releases[0].title == "[Unreleased]"
    # Unreleased is empty right after a version is recorded, so look at all versions
    assert any(release.sections.get("Added") for release in releases)


def test_results_are_grouped_and_ordered(tmp_path):
    write_result(tmp_path, "qa", "b2", "2026-11-02T10:00:00+00:00", {"f1": 0.6})
    write_result(tmp_path, "qa", "a1", "2026-11-01T10:00:00+00:00", {"f1": 0.5})
    write_result(tmp_path, "qa", "c3", "2026-11-03T10:00:00+00:00", {"f1": 0.7}, profile="gpu")
    [gpu, mac] = site_build.read_results(tmp_path)
    assert (mac.route, mac.profile, mac.datasets) == ("qa", "mac", "qasper abc123")
    assert [run["run_id"] for run in mac.runs] == ["a1", "b2"]
    assert mac.latest["metrics"] == {"f1": 0.6}
    assert mac.trend("f1") == [0.5, 0.6]
    assert len(gpu.runs) == 1


def test_trend_points():
    assert site_build.trend_points([0.5]) == ""
    assert site_build.trend_points([0.5, 1.0]) == "0.0,28.0 120.0,0.0"
    # Equal values give a flat line instead of a division by zero
    assert site_build.trend_points([0.7, 0.7]) == "0.0,28.0 120.0,28.0"


def test_without_results_the_page_says_so(tmp_path):
    page = site_build.render(PLAN, CHANGELOG, tmp_path)
    assert "No published results yet" in page


def test_a_version_without_changes_gets_a_note(tmp_path):
    changelog = "# Changelog\n\n## [Unreleased]\n\n## [0.0.2] - 2026-11-15\n\n### Added\n\n- A\n"
    page = site_build.render(PLAN, changelog, tmp_path)
    assert page.count("No changes since the last version yet.") == 1


def test_text_from_the_docs_is_escaped(tmp_path):
    plan = PLAN.replace("1.1 GitHub workflow |", "1.1 <script>alert(1)</script> |", 1)
    page = site_build.render(plan, CHANGELOG, tmp_path)
    assert "<script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_the_built_page_is_small_and_self_contained(tmp_path):
    write_result(tmp_path / "results", "qa", "a1", "2026-11-01T10:00:00+00:00", {"f1": 0.5})
    write_result(tmp_path / "results", "qa", "b2", "2026-11-02T10:00:00+00:00", {"f1": 0.6})
    page = site_build.build(tmp_path / "site", results_dir=tmp_path / "results")
    html = page.read_text()
    assert page.name == "index.html"
    assert page.stat().st_size < 1_000_000
    assert "<script" not in html and "<polyline" in html
    # Nothing is loaded from another site: no external scripts, styles, images or fonts
    assert not re.search(r'(src|href)="https?://(?!github\.com/mdu-ai-lab/)', html)
    assert "<link" not in html

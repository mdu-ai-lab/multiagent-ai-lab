# Checks the committed evaluation results in results/ against configs/eval/limits.yaml.
# For each limit, the newest published result of that route, profile and dataset must report
# the metric within its min and max. CI runs this on every push.
# Run: uv run python ops/eval_gate.py
# Exit code 0 when every limit holds. Without limits it passes and says so.

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from mrag.config import PROJECT_ROOT

LIMITS_FILE = PROJECT_ROOT / "configs" / "eval" / "limits.yaml"
RESULTS_DIR = PROJECT_ROOT / "results"
OK, FAIL = "OK", "FAIL"


class EvalGateError(Exception):
    pass


class Limit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: str
    profile: str
    dataset: str
    metric: str
    min: float | None = None
    max: float | None = None

    @model_validator(mode="after")
    def has_a_bound(self) -> "Limit":
        if self.min is None and self.max is None:
            raise ValueError("a limit needs min, max or both")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min is larger than max")
        return self

    def label(self) -> str:
        return f"{self.route} {self.profile} {self.dataset} {self.metric}"


class LimitsFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limits: list[Limit] = []

    @model_validator(mode="after")
    def each_limit_once(self) -> "LimitsFile":
        labels = [limit.label() for limit in self.limits]
        twice = sorted({label for label in labels if labels.count(label) > 1})
        if twice:
            raise ValueError(f"set more than once: {', '.join(twice)}")
        return self


@dataclass(frozen=True)
class Check:
    status: str
    name: str
    detail: str


def load_limits(path: Path = LIMITS_FILE) -> list[Limit]:
    data = yaml.safe_load(path.read_text()) or {}
    try:
        return LimitsFile.model_validate(data).limits
    except ValidationError as error:
        raise EvalGateError(f"{path.name} is not valid: {error}") from error


def load_results(results_dir: Path = RESULTS_DIR) -> list[dict[str, Any]]:
    # The files export_results.py writes: results/<route>/<date>_<run id>.json
    results = []
    for path in sorted(results_dir.glob("*/*.json")):
        try:
            results.append(json.loads(path.read_text()))
        except json.JSONDecodeError as error:
            raise EvalGateError(f"{path.name} is not valid JSON: {error}") from error
    return results


def newest_result(limit: Limit, results: list[dict[str, Any]]) -> dict[str, Any] | None:
    matching = [
        result
        for result in results
        if result.get("route") == limit.route
        and result.get("params", {}).get("profile") == limit.profile
        and f"dataset.{limit.dataset}" in result.get("params", {})
    ]
    return max(matching, key=lambda result: (result["started"], result["run_id"]), default=None)


def check_limit(limit: Limit, results: list[dict[str, Any]]) -> Check:
    result = newest_result(limit, results)
    if result is None:
        return Check(FAIL, limit.label(), "no published result in results/")
    run = f"run {result['run_id']} of {result['started'][:10]}"
    value = result.get("metrics", {}).get(limit.metric)
    # A missing or broken number must fail, never pass by accident
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        return Check(FAIL, limit.label(), f"{run} has no usable value for {limit.metric}")
    if limit.min is not None and value < limit.min:
        return Check(FAIL, limit.label(), f"{value:g} is below the minimum {limit.min:g} ({run})")
    if limit.max is not None and value > limit.max:
        return Check(FAIL, limit.label(), f"{value:g} is above the maximum {limit.max:g} ({run})")
    return Check(OK, limit.label(), f"{value:g} is within the limit ({run})")


def main() -> int:
    try:
        # The module values are read here, so tests can point them at other files
        limits = load_limits(LIMITS_FILE)
        results = load_results(RESULTS_DIR)
    except EvalGateError as error:
        print(error, file=sys.stderr)
        return 1
    if not limits:
        print("No limits in configs/eval/limits.yaml yet, so there is nothing to check")
        print("RESULT: OK (0 limits)")
        return 0
    checks = [check_limit(limit, results) for limit in limits]
    for check in checks:
        print(f"{check.status:4}  {check.name}: {check.detail}")
    failed = sum(check.status == FAIL for check in checks)
    if failed:
        print(f"RESULT: FAIL ({failed} of {len(checks)} limits)")
        return 1
    print(f"RESULT: OK ({len(checks)} limits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

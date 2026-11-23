"""Compare a fresh baseline run with the committed baseline summary.

The committed summary was produced in the pinned reference environment.  This
check fails when a fresh run changes a metric beyond a small tolerance, a fact
outcome, or the all-facts flag.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, cast


def load_summary(path: str | Path) -> dict[str, Any]:
    """Load a baseline summary JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("the baseline summary must be a JSON object")
    for key in ("metrics", "facts", "all_facts_pass"):
        if key not in data:
            raise ValueError(f"the baseline summary has no {key!r} field")
    return cast(dict[str, Any], data)


def compare_summaries(
    expected: dict[str, Any],
    actual: dict[str, Any],
    rtol: float = 1e-9,
    atol: float = 1e-12,
) -> list[str]:
    """Return every metric or fact difference between two summaries."""
    errors: list[str] = []
    expected_metrics = expected["metrics"]
    actual_metrics = actual["metrics"]
    for key, expected_value in expected_metrics.items():
        if key not in actual_metrics:
            errors.append(f"metric {key!r} is missing from the fresh run")
            continue
        actual_value = actual_metrics[key]
        if isinstance(expected_value, int) and not isinstance(expected_value, bool):
            if int(actual_value) != expected_value:
                errors.append(f"metric {key!r}: {actual_value} != {expected_value}")
            continue
        if not math.isclose(
            float(actual_value),
            float(expected_value),
            rel_tol=rtol,
            abs_tol=atol,
        ):
            errors.append(f"metric {key!r}: {actual_value} != {expected_value}")

    expected_facts = {row["statistic"]: bool(row["passes"]) for row in expected["facts"]}
    actual_facts = {row["statistic"]: bool(row["passes"]) for row in actual["facts"]}
    for label, passes in expected_facts.items():
        if label not in actual_facts:
            errors.append(f"fact {label!r} is missing from the fresh run")
        elif actual_facts[label] != passes:
            errors.append(f"fact {label!r}: {actual_facts[label]} != {passes}")

    if bool(actual["all_facts_pass"]) != bool(expected["all_facts_pass"]):
        errors.append(f"all_facts_pass: {actual['all_facts_pass']} != {expected['all_facts_pass']}")
    return errors


def compare_baseline(
    results: str | Path,
    expected_path: str | Path,
    rtol: float = 1e-9,
    atol: float = 1e-12,
) -> list[str]:
    """Compare ``results/metrics.json`` with the committed summary."""
    actual = load_summary(Path(results) / "metrics.json")
    expected = load_summary(expected_path)
    return compare_summaries(expected, actual, rtol=rtol, atol=atol)

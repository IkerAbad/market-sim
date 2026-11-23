"""Check the README results table against the committed baseline metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

STATISTIC_KEYS = {
    "Kurtosis": "kurtosis",
    "ACF(returns, lag 1)": "acf_return_lag1",
    "ACF(abs(returns), lag 1)": "acf_abs_return_lag1",
    "ACF(abs(returns), lag 50)": "acf_abs_return_lag50",
    "corr(volume, abs(returns))": "corr_volume_abs_return",
    "P(abs(r) > 4 sd) / P_normal": "tail_exceedance_ratio",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_baseline(root: Path) -> dict[str, Any]:
    data = json.loads(_read(root / "docs" / "baseline_metrics.json"))
    if not isinstance(data, dict):
        raise ValueError("docs/baseline_metrics.json must contain an object")
    return cast(dict[str, Any], data)


def parse_main_table(readme: str) -> list[dict[str, str]]:
    """Parse the six rows of the main results table."""
    if "## Results" not in readme:
        raise ValueError("README has no ## Results section")
    section = readme.split("## Results", 1)[1]
    if "### Reading the table" in section:
        section = section.split("### Reading the table", 1)[0]
    rows: list[dict[str, str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 5:
            continue
        if cells[0] == "Fact" or set(cells[0]) <= {"-", ":", " "}:
            continue
        rows.append(
            {
                "fact": cells[0],
                "statistic": cells[1],
                "value": cells[2],
                "criterion": cells[3],
                "pass": cells[4],
            }
        )
    return rows


def check_results(root: Path, rtol: float = 1e-3) -> list[str]:
    """Compare the README table with the committed baseline summary."""
    data = load_baseline(root)
    expected_metrics = data["metrics"]
    expected_facts = data["facts"]
    rows = parse_main_table(_read(root / "README.md"))
    errors: list[str] = []
    if len(rows) != len(expected_facts):
        errors.append(f"README has {len(rows)} rows, expected {len(expected_facts)}")
    for index, row in enumerate(rows):
        label = row["statistic"]
        key = STATISTIC_KEYS.get(label)
        if key is None:
            errors.append(f"README row {index + 1}: unknown statistic {label!r}")
            continue
        expected = float(expected_metrics[key])
        try:
            actual = float(row["value"])
        except ValueError:
            errors.append(f"README row {index + 1}: value is not numeric: {row['value']!r}")
            continue
        if abs(actual - expected) > rtol * max(abs(expected), 1e-12):
            errors.append(
                f"README row {index + 1} ({label}): {actual} != {expected} "
                f"(relative tolerance {rtol})"
            )
        expected_pass = bool(expected_facts[index]["passes"])
        actual_pass = row["pass"].lower() == "yes"
        if actual_pass != expected_pass:
            errors.append(
                f"README row {index + 1} ({label}): pass is {row['pass']!r}, "
                f"expected {'yes' if expected_pass else 'no'}"
            )
    return errors

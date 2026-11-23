"""Check that the numeric content of the README tables is reproduced.

Each table is compared with the generated report for its section.  A number in
the README must appear in the generated report within a small relative
tolerance.  This catches copied values that drift after a rerun.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

TOKEN_PATTERN = re.compile(r"\d+/\d+|[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?%?")

SECTION_SOURCES: dict[str, tuple[str, str]] = {
    "Results": ("file", "docs/baseline_metrics.json"),
    "Robustness across seeds": ("file", "docs/robustness.md"),
    "Statistical uncertainty": ("file", "docs/inference.md"),
    "Sample size": ("file", "docs/sample_size.md"),
    "Sensitivity": ("file", "docs/sensitivity.md"),
    "Ablations": ("file", "docs/ablations.md"),
    "Threshold sensitivity": ("file", "docs/thresholds.md"),
    "Additional facts": ("file", "docs/additional_facts.md"),
    "Synthetic benchmarks": ("file", "docs/benchmarks.md"),
    "Benchmark pass rates": ("file", "docs/benchmark_rates.md"),
    "Strict criteria on the hold-out": ("file", "docs/strict_criteria.md"),
    "Null distribution under Gaussian noise": ("file", "docs/null_distribution.md"),
    "Discrimination from the benchmarks": ("file", "docs/discrimination.md"),
    "Additional facts against the benchmarks": (
        "file",
        "docs/additional_discrimination.md",
    ),
    "Price and volume": ("file", "docs/price_volume.md"),
    "Block stability": ("file", "docs/stability.md"),
    "Block stability across seeds": ("file", "docs/block_ensemble.md"),
    "Resultados": ("english", "Results"),
    "Robustez": ("english", "Robustness across seeds"),
    "Ablaciones": ("english", "Ablations"),
    "Hechos adicionales": ("english", "Additional facts"),
    "Comparación con benchmarks": ("english", "Synthetic benchmarks"),
    "Tasa de aprobados de los benchmarks": ("english", "Benchmark pass rates"),
    "Criterios estrictos en la retención": ("english", "Strict criteria on the hold-out"),
    "Distribución nula con ruido gaussiano": (
        "english",
        "Null distribution under Gaussian noise",
    ),
    "Discriminación frente a los benchmarks": (
        "english",
        "Discrimination from the benchmarks",
    ),
    "Hechos adicionales frente a los benchmarks": (
        "english",
        "Additional facts against the benchmarks",
    ),
    "Estabilidad por bloques entre semillas": (
        "english",
        "Block stability across seeds",
    ),
}


@dataclass(frozen=True)
class ReadmeTable:
    heading: str
    rows: tuple[tuple[str, ...], ...]


def parse_tables(markdown: str) -> list[ReadmeTable]:
    """Return every Markdown table with its closest preceding heading."""
    lines = markdown.splitlines()
    heading = ""
    tables: list[ReadmeTable] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("#"):
            heading = line.strip("# ").strip()
            index += 1
            continue
        if not line.startswith("|"):
            index += 1
            continue
        rows: list[tuple[str, ...]] = []
        while index < len(lines) and lines[index].startswith("|"):
            cells = tuple(cell.strip() for cell in lines[index].strip().strip("|").split("|"))
            if not all(set(cell) <= {"-", ":", " "} for cell in cells):
                rows.append(cells)
            index += 1
        if rows:
            tables.append(ReadmeTable(heading=heading, rows=tuple(rows)))
    return tables


def numeric_values(text: str) -> list[float | str]:
    """Return the numeric tokens in a text, with percentages as fractions."""
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    values: list[float | str] = []
    for token in TOKEN_PATTERN.findall(text):
        if "/" in token:
            values.append(token)
            continue
        if token.endswith("%"):
            values.append(float(token[:-1]) / 100.0)
        else:
            values.append(float(token))
    return values


def _matches(left: float | str, right: float | str) -> bool:
    if isinstance(left, str) or isinstance(right, str):
        return left == right
    return math.isclose(left, right, rel_tol=1e-3, abs_tol=1e-9)


def _contains(values: list[float | str], needle: float | str) -> bool:
    return any(_matches(value, needle) for value in values)


def table_values(table: ReadmeTable) -> list[float | str]:
    values: list[float | str] = []
    for row in table.rows[1:]:
        for cell in row:
            values.extend(numeric_values(cell))
    return values


def check_readme_tables(root: Path) -> list[str]:
    """Return every README table value that is missing from its source."""
    readme = (root / "README.md").read_text(encoding="utf-8")
    tables = parse_tables(readme)
    by_heading: dict[str, list[ReadmeTable]] = {}
    for table in tables:
        by_heading.setdefault(table.heading, []).append(table)
    source_cache: dict[str, list[float | str]] = {}
    errors: list[str] = []
    for table in tables:
        source = SECTION_SOURCES.get(table.heading)
        if source is None:
            continue
        kind, reference = source
        if kind == "file":
            path = root / reference
            if not path.exists():
                errors.append(f"{table.heading}: source {reference} is missing")
                continue
            if reference.endswith(".json"):
                text = json.dumps(json.loads(path.read_text(encoding="utf-8")))
            else:
                text = path.read_text(encoding="utf-8")
            key = reference
        else:
            source_tables = by_heading.get(reference, [])
            if not source_tables:
                errors.append(f"{table.heading}: English table {reference!r} is missing")
                continue
            text = "\n".join(
                "|".join(cell for row in source_table.rows for cell in row)
                for source_table in source_tables
            )
            key = f"english:{reference}"
        if key not in source_cache:
            source_cache[key] = numeric_values(text)
        source_values = source_cache[key]
        for value in table_values(table):
            if not _contains(source_values, value):
                errors.append(f"{table.heading}: value {value!r} is not in the generated source")
    return errors

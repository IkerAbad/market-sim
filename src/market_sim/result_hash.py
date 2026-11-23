"""Stable hash of a baseline result directory.

The series is hashed after rounding every numeric column to six decimal
places.  The metrics are hashed after rounding every float to six significant
digits.  The raw ten-decimal series and the raw summary can differ in the last
bits between CPU microarchitectures because the SIMD math library is not the
same.  The published tables use four significant digits, so the canonical form
is still more precise than the published results.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .hashes import sha256_file

SERIES_DECIMALS = 6


def _canonical(value: Any) -> Any:
    if isinstance(value, float):
        return float(f"{value:.6g}")
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def canonical_metrics_hash(results: str | Path) -> str:
    """Return a platform-stable hash of the metrics summary."""
    path = Path(results) / "metrics.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(_canonical(data), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def canonical_series_hash(results: str | Path) -> str:
    """Return a platform-stable hash of the series at six decimal places."""
    path = Path(results) / "series.csv"
    lines: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        lines.append(",".join(header))
        for row in reader:
            values: list[str] = []
            for value in row:
                try:
                    number = float(value)
                except ValueError:
                    values.append(value)
                else:
                    values.append(f"{number:.{SERIES_DECIMALS}f}")
            lines.append(",".join(values))
    payload = "\n".join(lines) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def result_hashes(results: str | Path) -> dict[str, str]:
    """Return the canonical hashes and the raw series hash."""
    directory = Path(results)
    return {
        "metrics": canonical_metrics_hash(directory),
        "series": canonical_series_hash(directory),
        "raw_series": sha256_file(directory / "series.csv"),
    }


def combined_result_hash(results: str | Path) -> str:
    """Return one SHA256 over the canonical metrics and series hashes."""
    hashes = result_hashes(results)
    payload = f"{hashes['metrics']}:{hashes['series']}".encode("ascii")
    return hashlib.sha256(payload).hexdigest().upper()

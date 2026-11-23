"""Stable hash of a baseline result directory.

The series is hashed as written, with LF line endings.  The metrics are hashed
after rounding every float to six significant digits.  The raw summary differs
in the last bits between platforms because the math library is not the same.
The published metrics use four significant digits, so the canonical form is
still more precise than the tables.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .hashes import sha256_file


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


def result_hashes(results: str | Path) -> dict[str, str]:
    """Return the canonical metrics hash and the series hash."""
    directory = Path(results)
    return {
        "metrics": canonical_metrics_hash(directory),
        "series": sha256_file(directory / "series.csv"),
    }


def combined_result_hash(results: str | Path) -> str:
    """Return one SHA256 over the metrics hash and the series hash."""
    hashes = result_hashes(results)
    payload = f"{hashes['metrics']}:{hashes['series']}".encode("ascii")
    return hashlib.sha256(payload).hexdigest().upper()

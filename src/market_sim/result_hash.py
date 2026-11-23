"""Stable hash of a baseline result directory.

The hash is computed from the normalised text of ``metrics.json`` and
``series.csv``.  Two runs with the same seed should produce the same hash on
every platform and in every checkout.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .hashes import sha256_file


def result_hashes(results: str | Path) -> dict[str, str]:
    """Return the SHA256 of the metrics and the series files."""
    directory = Path(results)
    return {
        "metrics": sha256_file(directory / "metrics.json"),
        "series": sha256_file(directory / "series.csv"),
    }


def combined_result_hash(results: str | Path) -> str:
    """Return one SHA256 over the metrics hash and the series hash."""
    hashes = result_hashes(results)
    payload = f"{hashes['metrics']}:{hashes['series']}".encode("ascii")
    return hashlib.sha256(payload).hexdigest().upper()

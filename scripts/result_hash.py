"""Compute a stable hash of a baseline result directory.

Examples
--------
python scripts/result_hash.py --results results --output hash.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.result_hash import combined_result_hash, result_hashes  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    hashes = result_hashes(args.results)
    combined = combined_result_hash(args.results)
    print(f"metrics: {hashes['metrics']}")
    print(f"series:  {hashes['series']}")
    print(f"combined: {combined}")
    if args.output is not None:
        args.output.write_text(combined + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

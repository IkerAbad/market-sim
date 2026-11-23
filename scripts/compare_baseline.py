"""Compare a fresh baseline run with the committed summary.

Examples
--------
python scripts/compare_baseline.py --results results
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.baseline_check import compare_baseline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument(
        "--expected",
        type=Path,
        default=ROOT / "docs" / "baseline_metrics.json",
    )
    parser.add_argument("--rtol", type=float, default=1e-9)
    parser.add_argument("--atol", type=float, default=1e-12)
    args = parser.parse_args()
    errors = compare_baseline(
        args.results,
        args.expected,
        rtol=args.rtol,
        atol=args.atol,
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("fresh baseline matches docs/baseline_metrics.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

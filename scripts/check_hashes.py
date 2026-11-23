"""Check the committed output hashes.

Examples
--------
python scripts/check_hashes.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.hashes import check_hashes  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = check_hashes(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("committed output hashes match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

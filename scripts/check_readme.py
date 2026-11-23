"""Check that README table values appear in the generated reports.

Examples
--------
python scripts/check_readme.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.readme_tables import check_readme_tables  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = check_readme_tables(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("README table values match the generated reports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

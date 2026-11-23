"""Check that every version string in the repository agrees."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.version_check import check_versions  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = check_versions(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("version strings agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

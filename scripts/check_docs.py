"""Check local Markdown links and required documentation sections."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.docs import check_docs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = check_docs(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("documentation links are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

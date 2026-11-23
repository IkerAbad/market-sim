"""Generate or check the public API reference.

Examples
--------
python scripts/build_api_docs.py
python scripts/build_api_docs.py --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.api_docs import build_api_markdown, check_api_docs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "api.md")
    args = parser.parse_args()
    if args.check:
        errors = check_api_docs(ROOT)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("API reference is up to date")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_api_markdown(), encoding="utf-8")
    print(f"API reference: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

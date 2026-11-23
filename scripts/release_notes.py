"""Extract one release section from CHANGELOG.md.

Examples
--------
python scripts/release_notes.py --tag v0.4.0 --output release_notes.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.release import extract_release_notes  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="tag or version, e.g. v0.4.0")
    parser.add_argument(
        "--changelog",
        type=Path,
        default=Path("CHANGELOG.md"),
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    notes = extract_release_notes(args.changelog.read_text(encoding="utf-8"), args.tag)
    if args.output is None:
        print(notes, end="")
    else:
        args.output.write_text(notes, encoding="utf-8")
        print(f"release notes: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

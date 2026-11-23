"""Run every committed analysis in order.

Examples
--------
python scripts/reproduce_all.py --dry-run
python scripts/reproduce_all.py --jobs 8
python scripts/reproduce_all.py --skip-50-seeds
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.reproduce import full_commands, run_commands  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-50-seeds", action="store_true")
    args = parser.parse_args()
    commands = full_commands(
        jobs=args.jobs,
        include_50_seeds=not args.skip_50_seeds,
    )
    try:
        return run_commands(commands, dry_run=args.dry_run)
    except subprocess.CalledProcessError as exc:
        print(f"command failed with exit code {exc.returncode}: {exc.cmd}", file=sys.stderr)
        return exc.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())

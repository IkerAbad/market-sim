"""Thin wrapper around ``market_sim.cli.figures_main``."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.cli import figures_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(figures_main())

"""Market simulation loop and series input/output."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .agents import Population
from .config import SimulationConfig


@dataclass
class SimulationResult:
    """Output of one simulation run.

    ``returns[t]`` is the log return from step ``t`` to ``t + 1``.  ``prices``
    has one more element than ``returns`` because it stores the level at the
    start and at the end of every step.
    """

    config: SimulationConfig
    prices: np.ndarray
    returns: np.ndarray
    volume: np.ndarray

    def analysis_window(self) -> tuple[np.ndarray, np.ndarray]:
        """Return returns and volume after the burn-in period."""
        burn_in = self.config.burn_in
        return self.returns[burn_in:], self.volume[burn_in:]

    def price_window(self) -> np.ndarray:
        """Return log prices after the burn-in period."""
        return self.prices[self.config.burn_in :]


def simulate(config: SimulationConfig) -> SimulationResult:
    """Run the agent-based market for ``config.n_steps`` steps.

    The same configuration, including the seed, always produces the same
    arrays.  The random number generator is PCG64 through
    ``numpy.random.default_rng``.
    """
    rng = np.random.default_rng(config.seed)
    model = config.model
    population = Population.create(model, rng)

    n_steps = config.n_steps
    fundamental_log = math.log(model.fundamental_value)
    prices = np.empty(n_steps + 1, dtype=float)
    returns = np.empty(n_steps, dtype=float)
    volume = np.empty(n_steps, dtype=float)
    prices[0] = fundamental_log

    for t in range(n_steps):
        population.update_activity(rng)
        demand = population.demands(prices, t, fundamental_log, rng)
        net_demand = float(demand.mean())
        price_change = model.price_impact * net_demand
        returns[t] = price_change
        prices[t + 1] = prices[t] + price_change
        volume[t] = float(np.abs(demand).mean())

    if not (
        np.all(np.isfinite(prices)) and np.all(np.isfinite(returns)) and np.all(np.isfinite(volume))
    ):
        raise FloatingPointError("simulation produced a non-finite value")

    return SimulationResult(
        config=config,
        prices=prices,
        returns=returns,
        volume=volume,
    )


def save_series_csv(result: SimulationResult, path: str | Path) -> Path:
    """Write the analysed window to a CSV file with one row per step."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    burn_in = result.config.burn_in
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["step", "price", "log_price", "return", "volume"])
        for t in range(burn_in, result.config.n_steps):
            writer.writerow(
                [
                    t + 1,
                    f"{math.exp(result.prices[t + 1]):.10f}",
                    f"{result.prices[t + 1]:.10f}",
                    f"{result.returns[t]:.10f}",
                    f"{result.volume[t]:.10f}",
                ]
            )
    return path


def load_series_csv(path: str | Path) -> dict[str, np.ndarray]:
    """Load a series written by :func:`save_series_csv`."""
    columns: dict[str, list[float]] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("the CSV file has no header")
        for name in reader.fieldnames:
            columns[name] = []
        for row in reader:
            for name in reader.fieldnames:
                columns[name].append(float(row[name]))
    return {name: np.asarray(values, dtype=float) for name, values in columns.items()}

"""Wall-clock benchmark for the simulation loop."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace

from .config import SimulationConfig
from .market import simulate


@dataclass(frozen=True)
class BenchmarkResult:
    """Timing for one simulation length."""

    steps: int
    n_agents: int
    best_seconds: float
    mean_seconds: float
    runs: int

    @property
    def steps_per_second(self) -> float:
        return self.steps / self.mean_seconds

    @property
    def agent_steps_per_second(self) -> float:
        return self.steps * self.n_agents / self.mean_seconds


def time_simulation(config: SimulationConfig, steps: int, repeat: int = 1) -> BenchmarkResult:
    """Time ``repeat`` simulations of ``steps`` steps and return the summary."""
    if steps < 1:
        raise ValueError("steps must be positive")
    if repeat < 1:
        raise ValueError("repeat must be positive")
    benchmark_config = replace(config, n_steps=steps, burn_in=0)
    timings: list[float] = []
    for _ in range(repeat):
        start = time.perf_counter()
        simulate(benchmark_config)
        timings.append(time.perf_counter() - start)
    return BenchmarkResult(
        steps=steps,
        n_agents=config.model.n_agents,
        best_seconds=min(timings),
        mean_seconds=sum(timings) / len(timings),
        runs=repeat,
    )

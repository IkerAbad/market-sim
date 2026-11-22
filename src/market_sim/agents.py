"""Heterogeneous agent population.

Three behavioural types share the same accounting conventions:

* fundamentalists trade against the log gap between the fundamental value and
  the current price,
* chartists trade in the direction of the average return over their memory
  window,
* noise traders submit a zero-mean random demand.

Every agent has a memory, a risk-aversion coefficient and a persistent
activity state.  Risk aversion divides demand.  Activity multiplies demand and
follows a stationary log AR(1) process whose persistence is set by the agent's
memory.  The activity state represents attention or participation, not
wealth.  It is the only source of persistent stochastic volatility in the
model and its role is discussed in the README.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.random import Generator

from .config import ModelParams

FUNDAMENTALIST: Final[int] = 0
CHARTIST: Final[int] = 1
NOISE: Final[int] = 2

_ACTIVITY_CLIP: Final[float] = 50.0


@dataclass
class Population:
    """State of the heterogeneous agent population."""

    params: ModelParams
    kind: np.ndarray
    memory: np.ndarray
    risk_aversion: np.ndarray
    wealth: np.ndarray
    bias: np.ndarray
    rho: np.ndarray
    log_activity: np.ndarray
    activity: np.ndarray

    @classmethod
    def create(cls, params: ModelParams, rng: Generator) -> "Population":
        """Draw a population from ``params`` using ``rng``."""
        n = params.n_agents
        n_f = int(round(n * params.fundamentalist_fraction))
        n_c = int(round(n * params.chartist_fraction))
        n_f = min(n_f, n)
        n_c = min(n_c, n - n_f)

        kind = np.empty(n, dtype=np.int8)
        kind[:n_f] = FUNDAMENTALIST
        kind[n_f : n_f + n_c] = CHARTIST
        kind[n_f + n_c :] = NOISE

        memory = rng.integers(
            params.memory_min, params.memory_max + 1, size=n, dtype=np.int64
        )
        risk_aversion = rng.uniform(
            params.risk_aversion_min, params.risk_aversion_max, size=n
        )
        wealth = rng.uniform(params.wealth_min, params.wealth_max, size=n)
        wealth = wealth / wealth.mean()
        bias = rng.normal(0.0, params.fundamental_bias_std, size=n)

        rho = 1.0 - 1.0 / memory.astype(float)
        log_activity = rng.normal(0.0, params.activity_sigma, size=n)
        activity = np.exp(log_activity - 0.5 * params.activity_sigma**2)

        return cls(
            params=params,
            kind=kind,
            memory=memory,
            risk_aversion=risk_aversion,
            wealth=wealth,
            bias=bias,
            rho=rho,
            log_activity=log_activity,
            activity=activity,
        )

    def counts(self) -> dict[str, int]:
        """Number of agents of each type."""
        return {
            "fundamentalist": int(np.sum(self.kind == FUNDAMENTALIST)),
            "chartist": int(np.sum(self.kind == CHARTIST)),
            "noise": int(np.sum(self.kind == NOISE)),
        }

    def update_activity(self, rng: Generator) -> None:
        """Advance the persistent activity state by one step."""
        sigma = self.params.activity_sigma
        innovation = rng.normal(0.0, 1.0, size=self.kind.size)
        self.log_activity = (
            self.rho * self.log_activity
            + sigma * np.sqrt(1.0 - self.rho**2) * innovation
        )
        # The clip is a numerical guard for deliberately extreme test values.
        self.log_activity = np.clip(self.log_activity, -_ACTIVITY_CLIP, _ACTIVITY_CLIP)
        self.activity = np.exp(self.log_activity - 0.5 * sigma**2)

    def demands(
        self,
        prices: np.ndarray,
        t: int,
        fundamental_log: float,
        rng: Generator,
    ) -> np.ndarray:
        """Return the demand of every agent at time ``t``.

        ``prices`` is the full log-price path and ``t`` is the current index.
        Demands are expressed as fractions of initial wealth.
        """
        params = self.params
        demand = np.empty(self.kind.size, dtype=float)
        base = self.wealth / self.risk_aversion

        fundamentalists = self.kind == FUNDAMENTALIST
        if np.any(fundamentalists):
            gap = fundamental_log - prices[t]
            signal = params.kappa_fundamentalist * gap + self.bias[fundamentalists]
            demand[fundamentalists] = (
                base[fundamentalists]
                * params.max_fundamentalist_demand
                * np.tanh(signal / params.fundamental_scale)
            )

        chartists = self.kind == CHARTIST
        if np.any(chartists):
            lags = np.minimum(self.memory[chartists], t)
            lagged_price = prices[t - lags]
            trend = (prices[t] - lagged_price) / np.maximum(lags, 1)
            signal = params.kappa_chartist * trend
            demand[chartists] = (
                base[chartists]
                * params.max_chartist_demand
                * np.tanh(signal / params.chartist_scale)
            )

        noise = self.kind == NOISE
        if np.any(noise):
            demand[noise] = (
                base[noise]
                * params.noise_demand_scale
                * rng.normal(0.0, 1.0, size=int(np.sum(noise)))
            )

        return demand * self.activity

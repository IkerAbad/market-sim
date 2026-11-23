# Architecture

## Data flow

```text
configs/baseline.json
        |
        v
market_sim.config  ->  SimulationConfig
        |
        v
market_sim.agents  ->  Population
        |
        v
market_sim.market  ->  simulate  ->  SimulationResult
        |
        v
market_sim.stylized  ->  compute_metrics  ->  evaluate_facts
        |
        +--> scripts/run_simulation.py
        +--> scripts/make_figures.py
        +--> scripts/run_ensemble.py
        +--> scripts/run_inference.py
        +--> scripts/run_phase_diagram.py
        +--> scripts/run_ablations.py
        +--> scripts/run_sensitivity_full.py
        +--> scripts/run_thresholds.py
        +--> scripts/run_extra_facts.py
        +--> scripts/run_benchmarks.py
        +--> scripts/run_sample_size.py
        +--> scripts/run_price_volume.py
        +--> scripts/run_stability.py
```

## Modules

| Module | Responsibility |
| --- | --- |
| `agents.py` | Agent population, memory, risk aversion, activity and demand rules |
| `config.py` | Validated configuration dataclasses and JSON loading |
| `market.py` | Simulation loop, price impact and CSV input/output |
| `stylized.py` | Autocorrelation, kurtosis, correlation, tail ratio and the fact table |
| `plots.py` | The three figures |
| `ensemble.py` | Multi-seed runner, summaries and Wilson intervals |
| `bootstrap.py` | Moving-block bootstrap |
| `phase.py` | Two-dimensional parameter map |
| `ablations.py` | Component ablation study |
| `sensitivity.py` | One-at-a-time parameter sensitivity |
| `thresholds.py` | Threshold sensitivity over per-seed metrics |
| `benchmarks.py` | Gaussian, Student-t and GARCH benchmarks |
| `benchmark.py` | Wall-clock timing |
| `real_data.py` | User-supplied return or price series |
| `price_volume.py` | Price-gap and volume diagnostics |
| `sample_size.py` | Finite-sample sensitivity |
| `stability.py` | Block stability of the six statistics |
| `docs.py` | Local Markdown link checks |
| `release.py` | Release-note extraction from the changelog |
| `version_check.py` | Version consistency across metadata files |
| `results_check.py` | README table consistency against the baseline JSON |
| `api_docs.py` | API reference generation |
| `reproduce.py` | Ordered one-command reproduction |
| `cli.py` | `simulate`, `figures`, `ensemble` and `version` commands |

## Design rules

- Configuration is a frozen dataclass validated at construction time.
- The random generator is created once per run from the configured seed.
- The simulation loop has no global state and no file access.
- Statistics are pure functions of arrays.
- Reports are generated from the same functions that produce the tables.
- CI checks tests, types, links, versions, README values, API docs, the wheel,
  the container and the full baseline.

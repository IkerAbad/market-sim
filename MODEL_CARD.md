# Model card: market-sim

## Overview

`market-sim` is an agent-based toy model of a financial market.  It is built to
study whether a small set of behavioural rules can generate five stylized facts
of return series.  The model is not estimated from market data and is not a
forecasting system.

- Version: 0.4.0
- License: MIT
- Author: Iker Abad
- Repository: https://github.com/IkerAbad/market-sim

## Model details

The model has 200 agents in three groups:

- fundamentalists, who trade against the gap between the price and a constant
  fundamental value,
- chartists, who follow the average return over their memory window,
- noise traders, who submit a zero-mean random demand.

Each agent has a memory, a risk-aversion coefficient, a wealth weight and a
persistent activity state.  Activity follows a log AR(1) process whose
persistence is set by memory.  The price moves with a linear impact on net
demand.  Volume is gross demand.

The full equations are in `README.md` and `docs/robustness.md`.  Parameters and
the seed are in `configs/baseline.json`.

## Intended use

- Teaching agent-based models and stylized facts.
- Reproducible experiments on the effect of memory, activity and trend
  following.
- Testing statistical estimators, bootstrap methods and sensitivity analysis.
- A template for a small, auditable simulation repository.

## Out-of-scope use

- Forecasting real prices or volatility.
- Trading, investment advice or risk management.
- Calibration to a real asset.
- Policy analysis.
- Any decision with financial consequences.

## Data

All data are synthetic.  The model uses no personal data, no market data and no
external datasets.  The fundamental value is a constant chosen for the toy
model.

## Evaluation

The baseline run uses seed 20261122, 101,000 steps and a 1,000-step burn-in.
The five target facts pass under the stated thresholds.  A 20-seed hold-out,
using seeds not used to choose the parameters, also passes all six statistic
rows in 20 of 20 seeds.

The analysis is deliberately split into four layers:

- the single baseline table in `README.md`,
- the 20-seed distribution in `docs/robustness.md`,
- the moving-block bootstrap in `docs/inference.md`,
- the parameter map in `docs/phase_diagram.md`.

An extended 50-seed hold-out in `docs/robustness_50.md` passes all six rows in
50 of 50 seeds.  The 95% Wilson interval for the all-pass rate is
[0.929, 1.000].  The one-at-a-time parameter scan is in
`docs/sensitivity_full.md` and the threshold scan is in `docs/thresholds.md`.
A finite-sample scan passes at 10,000, 50,000, 100,000 and 200,000 steps.  The
price gap has an AR(1) half-life of 64.6 steps and the volume is heavy-tailed
and autocorrelated.  These diagnostics are in `docs/sample_size.md` and
`docs/price_volume.md`.  A GARCH(1,1) benchmark also passes the five price
facts, so the facts are not unique to the agent-based model.

Four additional diagnostics are in `docs/additional_facts.md`.  The model
reproduces the long-memory DFA exponent but not the leverage effect, gain/loss
asymmetry or volume lead-lag.

## What the ablation shows

`docs/ablations.md` removes one component at a time.  A noise-only version
passes all six statistic rows.  Removing activity leaves 1.33 rows on average
and no seed passes all six.  The three agent types are not the source of the
statistical facts.  They shape the price level and the return autocorrelation.
The activity process supplies the clustering and the tails.

This is a limitation of the behavioural interpretation.  The model is a
three-type market, but its stylized facts are mostly a property of the
persistent activity state.  A GARCH(1,1) benchmark also passes the five price
facts, so the five facts do not uniquely identify the agent-based model.  The
model's additional content is the endogenous volume and the explicit agent
rules.

## Limitations

- The fundamental value is constant.  The price is stationary and there are no
  long-run trends, bubbles or news.
- Volatility clustering comes from a reduced-form activity state, not from
  wealth dynamics or chartist herding.
- The three-type composition is not necessary for the statistical facts.  A
  noise-only ablation passes all six rows.
- A GARCH(1,1) benchmark also passes the five price facts.  The five facts do
  not uniquely identify the agent-based model.
- Chartists are deliberately weak.  Stronger chartists break the near-zero
  return autocorrelation.
- Volume is gross demand, so the volume-volatility correlation is partly
  mechanical.
- The slow decay of absolute-return autocorrelation is not true long memory.
- The model does not reproduce the leverage effect, gain/loss asymmetry or
  volume lead-lag.
- There is no order book, wealth update, dividend, short-selling constraint or
  transaction cost.
- Kurtosis is unstable in magnitude across seeds, although it stays above 3 in
  every seed of the hold-out.

## Ethical considerations

The model is a research and teaching artifact.  It must not be presented as
evidence about a real market.  Its outputs are synthetic and should not be used
to make financial decisions.  No personal data are processed.

## Reproduction

```bash
python -m pip install -e ".[dev]"
python scripts/run_simulation.py --config configs/baseline.json --output results
python scripts/make_figures.py --results results --output docs
python scripts/run_ensemble.py --config configs/baseline.json --seeds 1001-1020 --jobs 8
python -m pytest --cov=market_sim --cov-fail-under=98
```

The exact environment and output hashes are in `docs/reproducibility.md`.
Citation metadata is in `CITATION.cff`.

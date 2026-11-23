# Synthetic benchmarks

Command:

```
python scripts/run_benchmarks.py --config C:/dev/market-sim/configs/baseline.json --results C:/dev/market-sim/results --n 100000
```

- Observations per series: 100000
- The table uses the five price facts.  The volume fact is omitted
  because the benchmarks have no volume.
- The model row uses the same 100,000 returns as the main table.

| Series | Kurtosis | ACF(returns, 1) | ACF(abs, 1) | ACF(abs, 50) | Tail ratio | Facts passing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| market-sim baseline | 5.488 | -0.004945 | 0.1443 | 0.1176 | 32.21 | 5/5 |
| Gaussian | 3.02 | -0.007337 | 0.003022 | -0.003043 | 0.6315 | 2/5 |
| Student-t(5) | 8.18 | 0.0008168 | -0.008656 | -0.001822 | 58.25 | 3/5 |
| GARCH(1,1) | 4.096 | -0.0004496 | 0.1532 | 0.04533 | 22.58 | 5/5 |

## Reading

Gaussian returns fail the fat-tail and clustering facts.  Student-t
returns have fat tails but no volatility clustering.  GARCH(1,1) passes
the five price facts in this sample.  The five facts alone therefore do
not distinguish the agent-based model from a simple stochastic-volatility
benchmark.  The model's additional content is the endogenous volume and
the explicit agent rules.  The volume fact is not in this table because
the benchmarks have no volume.  The pass rates over 100 series per
process are in `docs/benchmark_rates.md`.

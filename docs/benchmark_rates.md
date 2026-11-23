# Benchmark pass rates

Command:

```
python scripts/run_benchmark_rates.py --config configs/baseline.json --series 100 --n 100000
```

- Series per synthetic benchmark: 100
- Observations per series: 100000
- Model row: 50 seeds from `docs/robustness_50.csv`
- The table uses the five price facts.  The volume fact is omitted
  because the synthetic benchmarks have no volume.

## Original criteria

| Series | Kurtosis | ACF(returns, 1) | ACF(abs, 1) | ACF(abs, 50) | Tail ratio | All five | 95% CI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| market-sim baseline | 50/50 | 50/50 | 50/50 | 50/50 | 50/50 | 50/50 | [0.93, 1.00] |
| Gaussian | 52/100 | 100/100 | 0/100 | 0/100 | 47/100 | 0/100 | [0.00, 0.04] |
| Student-t(5) | 100/100 | 100/100 | 0/100 | 0/100 | 100/100 | 0/100 | [0.00, 0.04] |
| GARCH(1,1) | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 | [0.96, 1.00] |

## Stricter criteria

Kurtosis above 5 and tail ratio above 10.  The other three criteria are
unchanged.  This table shows how the pass rates move when the two weak
tail criteria are tightened.

| Series | Kurtosis | ACF(returns, 1) | ACF(abs, 1) | ACF(abs, 50) | Tail ratio | All five | 95% CI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| market-sim baseline | 46/50 | 50/50 | 50/50 | 50/50 | 50/50 | 46/50 | [0.81, 0.97] |
| Gaussian | 0/100 | 100/100 | 0/100 | 0/100 | 0/100 | 0/100 | [0.00, 0.04] |
| Student-t(5) | 100/100 | 100/100 | 0/100 | 0/100 | 100/100 | 0/100 | [0.00, 0.04] |
| GARCH(1,1) | 5/100 | 100/100 | 100/100 | 100/100 | 100/100 | 5/100 | [0.02, 0.11] |

## Reading

Under the original criteria the Gaussian process passes the kurtosis
fact in about half of the samples.  A sample kurtosis above 3 is weak
evidence of fat tails at this sample size.  The tail ratio is also weak:
the Gaussian process passes it in about half of the samples.  The
clustering facts separate the processes cleanly.  GARCH(1,1) passes all
five original facts in every sample, so the original criteria do not
identify the agent-based model.

The stricter criteria tell a different story.  The model passes all five
in 46 of 50 seeds, GARCH passes in 5 of 100, and Gaussian and Student-t
pass in none.  Raising the two weak tail thresholds therefore separates
the agent-based model from the benchmarks.  The main table keeps the
original thresholds because they were fixed before these runs.  The
weakness of the original tail criteria is a documented limitation.
Repeating the benchmarks also shows that the single-series result in
`docs/benchmarks.md` is not a lucky draw.

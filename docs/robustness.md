# Robustness across seeds

Command:

```
python scripts/run_ensemble.py --config configs/baseline.json --seeds 1001-1020 --jobs 8
```

- Configuration: `configs/baseline.json`
- Seeds: 1001 to 1020 (20 seeds)
- Steps per seed: 101000, burn-in: 1000
- Seeds passing all six statistic rows: 20/20
- 95% Wilson interval for the all-pass rate: [0.839, 1.000]
- Per-seed values: `docs/robustness.csv`

| Statistic | Mean | Median | SD | Min | Max | 5% | 95% | Seeds passing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Kurtosis | 27.91 | 7.112 | 89.2 | 4.833 | 406.5 | 5.15 | 39.26 | 20/20 |
| ACF(returns, lag 1) | -0.003161 | -0.002353 | 0.00579 | -0.01542 | 0.01213 | -0.01004 | 0.00415 | 20/20 |
| ACF(abs(returns), lag 1) | 0.1954 | 0.183 | 0.0549 | 0.1423 | 0.3959 | 0.1483 | 0.2639 | 20/20 |
| ACF(abs(returns), lag 50) | 0.1328 | 0.1202 | 0.0386 | 0.08556 | 0.2351 | 0.09319 | 0.212 | 20/20 |
| corr(volume, abs(returns)) | 0.5627 | 0.549 | 0.0572 | 0.5093 | 0.7696 | 0.5096 | 0.6287 | 20/20 |
| Tail ratio | 50.98 | 51.31 | 9.53 | 34.1 | 69.62 | 35.15 | 69.32 | 20/20 |

## Reading

The baseline seed 20261122 is not in this set.  The seeds above were not
used to choose the parameters, so this table is a seed hold-out.  It
measures sampling variation, not variation in the model specification.
The pass counts use the same thresholds as the single-run table.

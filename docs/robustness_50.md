# Robustness across seeds

Command:

```
python scripts/run_ensemble.py --config configs/baseline.json --seeds 1001-1050 --jobs 8
```

- Configuration: `configs/baseline.json`
- Seeds: 1001 to 1050 (50 seeds)
- Steps per seed: 101000, burn-in: 1000
- Seeds passing all six statistic rows: 50/50
- 95% Wilson interval for the all-pass rate: [0.929, 1.000]
- Per-seed values: `docs/robustness_50.csv`

| Statistic | Mean | Median | SD | Min | Max | 5% | 95% | Seeds passing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Kurtosis | 15.35 | 6.304 | 56.5 | 4.564 | 406.5 | 4.9 | 14.56 | 50/50 |
| ACF(returns, lag 1) | -0.003744 | -0.003142 | 0.00477 | -0.01674 | 0.01213 | -0.01061 | 0.002676 | 50/50 |
| ACF(abs(returns), lag 1) | 0.1793 | 0.169 | 0.0426 | 0.1382 | 0.3959 | 0.1413 | 0.2345 | 50/50 |
| ACF(abs(returns), lag 50) | 0.1245 | 0.1126 | 0.0345 | 0.08188 | 0.2351 | 0.08453 | 0.1847 | 50/50 |
| corr(volume, abs(returns)) | 0.5469 | 0.5393 | 0.0457 | 0.4907 | 0.7696 | 0.4986 | 0.6086 | 50/50 |
| Tail ratio | 47.06 | 44.36 | 10.7 | 29.84 | 72.62 | 31.89 | 66.39 | 50/50 |

## Reading

The baseline seed 20261122 is not in this set.  The seeds above were not
used to choose the parameters, so this table is a seed hold-out.  It
measures sampling variation, not variation in the model specification.
The pass counts use the same thresholds as the single-run table.

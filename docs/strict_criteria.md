# Strict criteria on the 50-seed hold-out

Command:

```
python scripts/run_strict_criteria.py --config configs/baseline.json --input docs/robustness_50.csv
```

- Seeds: 50
- Strict criteria: kurtosis > 5, tail ratio > 10, other three criteria unchanged
- Seeds passing all five: 46/50 (92.0%), 95% CI [0.812, 0.968]

| Fact | Criterion | Passes | 95% CI |
| --- | --- | ---: | ---: |
| Kurtosis | > 5 | 46/50 | [0.812, 0.968] |
| ACF(returns, 1) | abs(value) < 0.05 | 50/50 | [0.929, 1.000] |
| ACF(abs, 1) | > 0.05 | 50/50 | [0.929, 1.000] |
| ACF(abs, 50) | > 0.02 | 50/50 | [0.929, 1.000] |
| Tail ratio | > 10 | 50/50 | [0.929, 1.000] |
| All five | - | 46/50 | [0.812, 0.968] |

| Seed | Failing facts | Kurtosis | Tail ratio |
| ---: | --- | ---: | ---: |
| 1012 | Kurtosis | 4.833 | 35.21 |
| 1031 | Kurtosis | 4.759 | 31.89 |
| 1035 | Kurtosis | 4.564 | 29.84 |
| 1046 | Kurtosis | 4.982 | 34.26 |

## Reading

The strict thresholds remove the false positives that the original
kurtosis and tail-ratio criteria admit.  In this hold-out the only
failures are kurtosis values between 4.56 and 4.98, just below 5.
The other four facts pass on every seed.  The main results table keeps
the original thresholds because they were fixed before the benchmark
runs.  This report is the stricter companion table.

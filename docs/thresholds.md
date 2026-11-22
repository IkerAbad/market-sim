# Threshold sensitivity

Command:

```
python scripts/run_thresholds.py --input docs/robustness.csv --report docs/thresholds.md --csv docs/thresholds.csv
```

- Per-seed metrics: `docs/robustness.csv`
- Seeds: 20
- Each row uses the same per-seed metrics and changes only the
  threshold of one fact.

| Fact | Threshold | Seeds passing | Pass rate |
| --- | ---: | ---: | ---: |
| Kurtosis | > 3 | 20/20 | 100% |
| Kurtosis | > 5 | 19/20 | 95% |
| Kurtosis | > 10 | 4/20 | 20% |
| Kurtosis | > 20 | 1/20 | 5% |
| ACF(returns, 1) | |value| < 0.01 | 18/20 | 90% |
| ACF(returns, 1) | |value| < 0.02 | 20/20 | 100% |
| ACF(returns, 1) | |value| < 0.05 | 20/20 | 100% |
| ACF(returns, 1) | |value| < 0.1 | 20/20 | 100% |
| ACF(abs, 1) | > 0.05 | 20/20 | 100% |
| ACF(abs, 1) | > 0.1 | 20/20 | 100% |
| ACF(abs, 1) | > 0.15 | 18/20 | 90% |
| ACF(abs, 1) | > 0.2 | 6/20 | 30% |
| ACF(abs, 50) | > 0.02 | 20/20 | 100% |
| ACF(abs, 50) | > 0.05 | 20/20 | 100% |
| ACF(abs, 50) | > 0.1 | 18/20 | 90% |
| ACF(abs, 50) | > 0.15 | 4/20 | 20% |
| corr(volume, abs) | > 0.2 | 20/20 | 100% |
| corr(volume, abs) | > 0.3 | 20/20 | 100% |
| corr(volume, abs) | > 0.5 | 20/20 | 100% |
| corr(volume, abs) | > 0.6 | 3/20 | 15% |
| Tail ratio | > 1 | 20/20 | 100% |
| Tail ratio | > 5 | 20/20 | 100% |
| Tail ratio | > 20 | 20/20 | 100% |
| Tail ratio | > 50 | 12/20 | 60% |

## Reading

A high pass rate under a stricter threshold means the fact has a
large margin.  A low pass rate means the conclusion depends on the
original cut-off.  The strictest cell in this table is
Kurtosis at 5% (1/20).

# Null distribution under Gaussian noise

Command:

```
python scripts/run_null_distribution.py --config configs/baseline.json --series 1000 --n 100000
```

- Gaussian series: 1000
- Observations per series: 100000
- ACF computed up to lag 50
- Model metrics: `docs/baseline_metrics.json`

| Statistic | Gaussian 5% | Median | 95% | Model | Model percentile |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kurtosis | 2.975 | 3.001 | 3.028 | 5.488 | 100.0% |
| ACF(returns, 1) | -0.004923 | 0.000226 | 0.005366 | -0.004945 | 5.0% |
| ACF(abs, 1) | -0.004767 | -0.0001644 | 0.005291 | 0.1443 | 100.0% |
| ACF(abs, 50) | -0.005107 | -6.039e-06 | 0.005015 | 0.1176 | 100.0% |
| Tail ratio | 0.4736 | 0.9472 | 1.737 | 32.21 | 100.0% |

## Reading

The 5% and 95% columns are the quantiles of each statistic over
independent Gaussian series of the same length.  The last column is the
fraction of Gaussian series below the model value.

The kurtosis threshold of 3 sits at the median of the Gaussian null, so
about half of Gaussian samples pass it.  The model value 5.488 is far
outside the 95% quantile.  The same happens with the tail ratio.  The
return autocorrelation is small in magnitude, near the 5% quantile of
the Gaussian null, as intended.  The absolute-return autocorrelations
are far above the Gaussian 95% quantile, which is the part of the table
that the benchmarks do not reproduce with a simple Gaussian process.

# Sample-size sensitivity

Command:

```
python scripts/run_sample_size.py --config configs/baseline.json --sizes 10000,50000,100000,200000 --seeds 1001-1003 --jobs 8
```

- Seeds per size: 3
- Each row uses the same model and a different number of simulated steps.

| Size | Seeds | Mean kurtosis | Mean ACF(returns, 1) | Mean ACF(abs, 1) | Mean ACF(abs, 50) | Mean corr | Mean tail | Mean pass | All-pass seeds |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10000 | 3 | 5.987 | 0.0035 | 0.1620 | 0.0980 | 0.5308 | 48.53 | 6.00 | 3/3 |
| 50000 | 3 | 12.090 | -0.0045 | 0.1943 | 0.1479 | 0.5602 | 47.68 | 6.00 | 3/3 |
| 100000 | 3 | 11.542 | -0.0036 | 0.2048 | 0.1564 | 0.5728 | 51.77 | 6.00 | 3/3 |
| 200000 | 3 | 9.263 | -0.0048 | 0.1907 | 0.1450 | 0.5586 | 49.16 | 6.00 | 3/3 |

## Reading

Kurtosis is the most sample-dependent statistic because it is driven
by rare large returns.  The autocorrelations, the volume correlation
and the tail ratio are expected to be more stable.  The table shows
whether the 100,000-step baseline is a special case or one point on
a stable curve.

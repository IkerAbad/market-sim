# Bootstrap intervals

Command:

```
python scripts/run_inference.py --config configs/baseline.json --results results --resamples 200 --block-length 1000 --seed 12345
```

- Observations: 100000
- Bootstrap resamples: 200
- Block length: 1000
- Bootstrap seed: 12345

| Statistic | Point estimate | Bootstrap mean | 95% interval |
| --- | ---: | ---: | ---: |
| Kurtosis | 5.488 | 5.521 | [4.235, 7.693] |
| ACF(returns, lag 1) | -0.004945 | -0.00504 | [-0.0125, 0.003521] |
| ACF(abs(returns), lag 1) | 0.1443 | 0.1442 | [0.1145, 0.1814] |
| ACF(abs(returns), lag 50) | 0.1176 | 0.1125 | [0.08772, 0.1444] |
| corr(volume, abs(returns)) | 0.5016 | 0.5021 | [0.4741, 0.5382] |
| Tail ratio | 32.21 | 32.31 | [23.52, 44.54] |

## Reading

The bootstrap resamples contiguous blocks of consecutive observations and
recomputes each statistic.  The interval measures within-series sampling
uncertainty.  It does not include parameter uncertainty, model uncertainty
or variation across seeds.  That last source is measured in
`docs/robustness.md`.

The block length is 1000, well above the largest lag used here (50).
Shorter blocks would attenuate the autocorrelation at long lags.

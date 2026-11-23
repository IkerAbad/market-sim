# Discrimination between the model and the benchmarks

Command:

```
python scripts/run_discrimination.py --config configs/baseline.json --series 100 --n 100000
```

- Model sample: 50 seeds from `docs/robustness_50.csv`
- GARCH and Gaussian samples: 100 series each
- Observations per synthetic series: 100000
- AUC is the probability that a random model value is on the model side
  of a random benchmark value.  0.5 means no separation.

## Area under the ROC curve

| Statistic | Model median | GARCH median | Gaussian median | AUC vs GARCH | AUC vs Gaussian |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kurtosis | 6.304 | 4.28 | 3 | 0.962 | 1.000 |
| ACF(returns, 1) | -0.003142 | 0.000766 | 0.0002724 | 0.426 | 0.351 |
| ACF(abs, 1) | 0.169 | 0.1674 | -2.617e-05 | 0.517 | 1.000 |
| ACF(abs, 50) | 0.1126 | 0.05986 | -3.298e-05 | 0.989 | 1.000 |
| Tail ratio | 44.36 | 25.73 | 0.9472 | 0.985 | 1.000 |

## Threshold grid

The table reports the all-five pass rate over kurtosis and tail-ratio
thresholds.  The other three criteria are fixed.  The figure
`docs/discrimination.png` shows the same grid as heatmaps.

| Kurtosis > | Tail ratio > | Model | GARCH | Gaussian |
| ---: | ---: | ---: | ---: | ---: |
| 3 | 1 | 50/50 | 100/100 | 0/100 |
| 3 | 2 | 50/50 | 100/100 | 0/100 |
| 3 | 5 | 50/50 | 100/100 | 0/100 |
| 3 | 10 | 50/50 | 100/100 | 0/100 |
| 3 | 20 | 50/50 | 94/100 | 0/100 |
| 3 | 50 | 21/50 | 0/100 | 0/100 |
| 4 | 1 | 50/50 | 93/100 | 0/100 |
| 4 | 2 | 50/50 | 93/100 | 0/100 |
| 4 | 5 | 50/50 | 93/100 | 0/100 |
| 4 | 10 | 50/50 | 93/100 | 0/100 |
| 4 | 20 | 50/50 | 92/100 | 0/100 |
| 4 | 50 | 21/50 | 0/100 | 0/100 |
| 5 | 1 | 46/50 | 5/100 | 0/100 |
| 5 | 2 | 46/50 | 5/100 | 0/100 |
| 5 | 5 | 46/50 | 5/100 | 0/100 |
| 5 | 10 | 46/50 | 5/100 | 0/100 |
| 5 | 20 | 46/50 | 5/100 | 0/100 |
| 5 | 50 | 21/50 | 0/100 | 0/100 |
| 6 | 1 | 26/50 | 2/100 | 0/100 |
| 6 | 2 | 26/50 | 2/100 | 0/100 |
| 6 | 5 | 26/50 | 2/100 | 0/100 |
| 6 | 10 | 26/50 | 2/100 | 0/100 |
| 6 | 20 | 26/50 | 2/100 | 0/100 |
| 6 | 50 | 21/50 | 0/100 | 0/100 |
| 8 | 1 | 14/50 | 2/100 | 0/100 |
| 8 | 2 | 14/50 | 2/100 | 0/100 |
| 8 | 5 | 14/50 | 2/100 | 0/100 |
| 8 | 10 | 14/50 | 2/100 | 0/100 |
| 8 | 20 | 14/50 | 2/100 | 0/100 |
| 8 | 50 | 13/50 | 0/100 | 0/100 |
| 10 | 1 | 9/50 | 1/100 | 0/100 |
| 10 | 2 | 9/50 | 1/100 | 0/100 |
| 10 | 5 | 9/50 | 1/100 | 0/100 |
| 10 | 10 | 9/50 | 1/100 | 0/100 |
| 10 | 20 | 9/50 | 1/100 | 0/100 |
| 10 | 50 | 8/50 | 0/100 | 0/100 |

## Reading

Kurtosis separates the model from GARCH with AUC 0.962.
ACF(abs, 50) separates them with AUC 0.989.
ACF(abs, 1) is close to a coin flip, with AUC 0.517.
The two clustering facts are not equally informative: the slow
autocorrelation is the stronger discriminator.

At kurtosis > 5 and tail ratio > 10 the model passes all five in 46/50 seeds, GARCH in
5/100 and Gaussian in 0/100.  At kurtosis > 4 the model passes 50/50 and GARCH 93/100.
The separation is sharpest between 4 and 5, where GARCH loses almost all of its passes
while the model keeps most of them.  The grid is a sensitivity map, not a licence to
choose the best cell after seeing the data.  The strict thresholds were fixed from the
benchmark pass rates before this grid was computed.

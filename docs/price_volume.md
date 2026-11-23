# Price and volume diagnostics

Command:

```
python scripts/run_price_volume.py --config C:/dev/market-sim/configs/baseline.json --results results
```

- Observations: 100000
- Fundamental value: 100

| Statistic | Value |
| --- | ---: |
| Minimum price | 89.35 |
| Maximum price | 111.6 |
| Final price | 98.29 |
| Mean log gap | -0.002646 |
| Log gap standard deviation | 0.02011 |
| Minimum log gap | -0.1127 |
| Maximum log gap | 0.1094 |
| Log gap AR(1) coefficient | 0.9893 |
| Log gap half-life (steps) | 64.64 |
| Mean volume | 0.2126 |
| Volume standard deviation | 0.05421 |
| Volume kurtosis | 5.99 |
| Volume ACF(1) | 0.5746 |
| Volume ACF(10) | 0.559 |
| corr(volume, abs(returns)) | 0.5016 |

## Reading

These are descriptive diagnostics, not target facts.  The price gap is
stationary around the constant fundamental value.  Its AR(1) coefficient
and half-life describe how quickly the fundamentalists pull the price
back.  The volume is heavy-tailed and autocorrelated.  Its correlation
with absolute returns is the quantity used in fact 4.

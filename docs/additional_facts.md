# Additional stylized facts

Command:

```
python scripts/run_extra_facts.py --results results --report docs/additional_facts.md --csv docs/additional_facts.csv
```

- Observations: 100000
- Additional facts passing: 2/5

| Additional fact | Statistic | Value | Criterion | Pass |
| --- | --- | ---: | --- | :---: |
| Leverage effect | corr(r[t], abs(r[t+1])) | -0.0009623 | < -0.02 | no |
| Gain/loss asymmetry | std(losses) / std(gains) | 1 | > 1.05 | no |
| Long memory of abs(returns) | DFA Hurst exponent | 0.8548 | > 0.60 | yes |
| Volume leads volatility | best lag of corr(volume, abs(return)) | 0 | > 0 | no |
| Aggregational Gaussianity | kurtosis(60-step) / kurtosis(1-step) | 0.6107 | < 1 | yes |

## Kurtosis by horizon

Returns are summed over disjoint blocks of the given length.  A model
with aggregational Gaussianity shows a kurtosis that falls towards three
as the horizon grows.

| Horizon (steps) | Kurtosis |
| ---: | ---: |
| 1 | 5.488 |
| 5 | 5.25 |
| 20 | 4.916 |
| 60 | 3.351 |

## Reading

These diagnostics are not part of the original five facts.  They are
reported to show what the model does not reproduce.  A failure here is a
limitation of the model, not a bug in the simulator.  The thresholds are
explicit choices, like the thresholds in the main table.

The leverage effect is the correlation between a return and the next
absolute return.  A negative value is the usual sign.  Gain/loss
asymmetry compares the volatility of negative and positive returns.
The DFA exponent measures long-range persistence in absolute returns.
The volume lead-lag diagnostic finds the lag that maximises
`corr(volume[t], abs(return[t + lag]))`.  Aggregational Gaussianity
compares the kurtosis of 60-step returns with the kurtosis of one-step
returns.

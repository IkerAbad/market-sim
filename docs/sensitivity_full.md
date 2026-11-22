# One-at-a-time sensitivity

Command:

```
python scripts/run_sensitivity_full.py --config configs/baseline.json --seeds 1001-1003 --steps 101000 --burn-in 1000 --jobs 8
```

- Seeds per variant: 3
- Each cell is the number of seeds where that statistic passes.
- The baseline row is the reference.
- Variants with all seeds passing: baseline, activity_0.75, activity_1.25, chartist_0.05, chartist_0.20, chartist_off, impact_0.025, impact_0.100, impact_0.200, noise_0.5, noise_2.0, noise_5.0, risk_low, risk_high, risk_very_high, memory_long, bias_0.0, bias_0.1, bias_0.5, wealth_equal, fundamental_kappa_0.5, fundamental_kappa_2.0, fundamental_max_0.5, fundamental_max_2.0, fundamental_off.
- Variants with at least one failing seed: activity_0.5, activity_2.0, chartist_0.50, chartist_1.00, risk_very_low, memory_very_short, memory_short.

| Variant | Kurtosis | ACF(returns, 1) | ACF(abs, 1) | ACF(abs, 50) | corr(volume, abs) | Tail ratio | Mean pass | All-pass seeds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| activity_0.5 | 3/3 | 3/3 | 0/3 | 2/3 | 3/3 | 3/3 | 4.67 | 0/3 |
| activity_0.75 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| activity_1.25 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| activity_2.0 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 | 5.67 | 2/3 |
| chartist_0.05 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| chartist_0.20 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| chartist_0.50 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 | 5.67 | 2/3 |
| chartist_1.00 | 3/3 | 0/3 | 3/3 | 3/3 | 1/3 | 3/3 | 4.33 | 0/3 |
| chartist_off | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| impact_0.025 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| impact_0.100 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| impact_0.200 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| noise_0.5 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| noise_2.0 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| noise_5.0 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| risk_low | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| risk_high | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| risk_very_low | 3/3 | 0/3 | 3/3 | 3/3 | 3/3 | 3/3 | 5.00 | 0/3 |
| risk_very_high | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| memory_very_short | 3/3 | 0/3 | 3/3 | 0/3 | 3/3 | 3/3 | 4.00 | 0/3 |
| memory_short | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 5.67 | 2/3 |
| memory_long | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| bias_0.0 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| bias_0.1 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| bias_0.5 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| wealth_equal | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| fundamental_kappa_0.5 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| fundamental_kappa_2.0 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| fundamental_max_0.5 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| fundamental_max_2.0 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| fundamental_off | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |

## Reading

This is a one-at-a-time scan, not a full factorial design.  A variant
with a lower mean pass count identifies a parameter that the facts
depend on.  The baseline row uses the same seeds as the other rows.

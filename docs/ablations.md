# Ablation study

Command:

```
python scripts/run_ablations.py --config configs/baseline.json --seeds 1001-1003 --steps 101000 --burn-in 1000 --jobs 8
```

- Seeds per ablation: 3
- Each cell is the number of seeds where that statistic passes.
- The baseline row is the reference.

| Ablation | Kurtosis | ACF(returns, 1) | ACF(abs, 1) | ACF(abs, 50) | corr(volume, abs) | Tail ratio | Mean pass | All-pass seeds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| no_chartists | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| no_fundamentalists | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| noise_only | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| no_activity | 0/3 | 3/3 | 0/3 | 0/3 | 0/3 | 1/3 | 1.33 | 0/3 |
| fixed_memory | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| homogeneous_risk | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| homogeneous_wealth | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| no_bias | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6.00 | 3/3 |
| no_noise_demand | 3/3 | 0/3 | 3/3 | 3/3 | 3/3 | 3/3 | 5.00 | 0/3 |

## Reading

- `noise_only`: 6.00/6, all-pass 3/3.
- `no_chartists`: 6.00/6, all-pass 3/3.
- `no_fundamentalists`: 6.00/6, all-pass 3/3.
- `no_activity`: 1.33/6, all-pass 0/3.
- `no_noise_demand`: 5.00/6, all-pass 0/3.

The three-type composition is not necessary for the six rows: the
noise-only variant passes all of them.  The activity process is
necessary: removing it removes most of the rows.  The agent types
shape the price level and the return autocorrelation, but they are
not the source of the statistical facts.

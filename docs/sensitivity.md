# Sensitivity

Every row uses 101,000 simulated steps with a 1,000-step burn-in, so the
statistics are computed on 100,000 observations.  Only the listed parameter
changes with respect to `configs/baseline.json`.  The table has six statistic
rows because fact 3 is split into its lag-1 and lag-50 autocorrelations.

| Variant | Change | Kurtosis | ACF1 | ACF(abs,1) | ACF(abs,50) | corr(volume,abs) | Tail ratio | Rows passing |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | seed 20261122, activity_sigma 1.0, max_chartist_demand 0.1 | 5.488 | -0.0049 | 0.1443 | 0.1176 | 0.5016 | 32.21 | 6/6 |
| Strong chartists | max_chartist_demand 0.5 | 5.289 | 0.0505 | 0.1407 | 0.1133 | 0.4513 | 30.94 | 5/6 |
| Very strong chartists | max_chartist_demand 1.0 | 5.507 | 0.9103 | 0.8570 | 0.7377 | 0.1436 | 16.42 | 4/6 |
| Low activity | activity_sigma 0.5 | 3.131 | -0.0035 | 0.0156 | 0.0208 | 0.2462 | 2.53 | 5/6 |
| Alternative seed | seed 7 | 4.523 | -0.0045 | 0.1219 | 0.0809 | 0.4672 | 26.68 | 6/6 |

Commands:

```bash
python scripts/run_simulation.py --config configs/baseline.json --output results
python scripts/run_simulation.py --config configs/baseline.json --set model.max_chartist_demand=0.5 --output results_chartists_05
python scripts/run_simulation.py --config configs/baseline.json --set model.max_chartist_demand=1.0 --output results_chartists_10
python scripts/run_simulation.py --config configs/baseline.json --set model.activity_sigma=0.5 --output results_low_activity
python scripts/run_simulation.py --config configs/baseline.json --seed 7 --output results_seed7
```

## Reading

- Chartist strength controls the return-autocorrelation trade-off.  Raising
  `max_chartist_demand` from 0.1 to 0.5 pushes ACF1 to 0.0505, just above the
  0.05 threshold.  At 1.0 the returns become strongly autocorrelated
  (ACF1 = 0.9103) and the volume correlation falls to 0.1436.  Strong trend
  following is incompatible with fact 2 in this model.
- Activity volatility controls clustering and most of the excess kurtosis.
  With `activity_sigma = 0.5`, kurtosis falls to 3.131 and the lag-1
  autocorrelation of absolute returns falls to 0.0156, so fact 3 fails.
- The seed changes the magnitudes but not the qualitative outcome for the
  baseline parameters.  Kurtosis moves from 5.488 to 4.523 and ACF(abs,50)
  from 0.1176 to 0.0809.  A single seed is not a robust estimate of a
  population moment.

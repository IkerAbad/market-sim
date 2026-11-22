# Parameter robustness map

Command:

```
python scripts/run_phase_diagram.py --config configs/baseline.json --activity 0.5,0.75,1.0,1.25,1.5 --chartist 0.05,0.1,0.2,0.5,1.0 --seeds 1-3 --steps 30000 --burn-in 1000 --jobs 8
```

- Seeds per cell: 3
- Cells show the mean number of passing statistic rows and, in
  parentheses, the number of seeds where all six rows pass.
- The red outline marks the baseline cell.

| max_chartist_demand \ activity_sigma | 0.5 | 0.75 | 1 | 1.25 | 1.5 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.05 | 4.33 (0/3) | 5.67 (2/3) | 6.00 (3/3) | 6.00 (3/3) | 6.00 (3/3) |
| 0.1 | 4.33 (0/3) | 5.67 (2/3) | 6.00 (3/3) | 6.00 (3/3) | 6.00 (3/3) |
| 0.2 | 4.33 (0/3) | 5.67 (2/3) | 6.00 (3/3) | 6.00 (3/3) | 6.00 (3/3) |
| 0.5 | 4.00 (0/3) | 5.33 (1/3) | 5.33 (1/3) | 5.33 (1/3) | 5.33 (1/3) |
| 1 | 3.33 (0/3) | 3.33 (0/3) | 3.33 (0/3) | 4.33 (0/3) | 5.00 (0/3) |

## Reading

This is a coarse scan, not the 100,000-step baseline.  It shows the
region where the model satisfies the criteria and the two main
failure directions.  Low activity reduces clustering and breaks fact
3.  High chartist demand creates return autocorrelation and breaks
fact 2.

# Performance

Command:

```
python scripts/run_benchmark.py --config configs/baseline.json --steps 10000,50000,100000 --repeat 1
```

- Reference machine: Ryzen 9 5900X, 32 GB DDR4-3600, Windows 11.
- Timing includes only the simulation loop, not metrics, figures or bootstrap.

| Steps | Runs | Best time (s) | Mean time (s) | Steps/s | Agent-steps/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10000 | 1 | 0.560 | 0.560 | 17,844 | 3,568,762 |
| 50000 | 1 | 2.800 | 2.800 | 17,856 | 3,571,268 |
| 100000 | 1 | 5.538 | 5.538 | 18,058 | 3,611,519 |

## Reading

The 100,000-step row is the size of the baseline run.  The table is a
rough measure of how long a full configuration takes on the reference
machine.  It is not a performance guarantee for other hardware.

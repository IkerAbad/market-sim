# Block stability across seeds

Command:

```
python scripts/run_block_ensemble.py --config configs/baseline.json --seeds 1001-1020 --blocks 10 --jobs 8
```

- Seeds: 20
- Blocks per seed: 10
- Total blocks: 200
- Seeds with every block passing all six statistics: 19/20

| Seed | Blocks passing all six | All blocks |
| ---: | ---: | :---: |
| 1001 | 10/10 | yes |
| 1002 | 10/10 | yes |
| 1003 | 10/10 | yes |
| 1004 | 10/10 | yes |
| 1005 | 10/10 | yes |
| 1006 | 10/10 | yes |
| 1007 | 10/10 | yes |
| 1008 | 10/10 | yes |
| 1009 | 10/10 | yes |
| 1010 | 10/10 | yes |
| 1011 | 10/10 | yes |
| 1012 | 10/10 | yes |
| 1013 | 10/10 | yes |
| 1014 | 10/10 | yes |
| 1015 | 10/10 | yes |
| 1016 | 10/10 | yes |
| 1017 | 10/10 | yes |
| 1018 | 10/10 | yes |
| 1019 | 10/10 | yes |
| 1020 | 9/10 | no |

| Statistic | Blocks passing | Rate | 95% CI |
| --- | ---: | ---: | ---: |
| Kurtosis | 200/200 | 100.0% | [98.1%, 100.0%] |
| ACF(returns, lag 1) | 199/200 | 99.5% | [97.2%, 99.9%] |
| ACF(abs(returns), lag 1) | 200/200 | 100.0% | [98.1%, 100.0%] |
| ACF(abs(returns), lag 50) | 200/200 | 100.0% | [98.1%, 100.0%] |
| corr(volume, abs(returns)) | 200/200 | 100.0% | [98.1%, 100.0%] |
| P(abs(r) > 4 sd) / P_normal | 200/200 | 100.0% | [98.1%, 100.0%] |

## Reading

This table extends `docs/stability.md` from one seed to the full seed
set.  Each block is a contiguous slice of one simulated series, so the
block pass rate measures stability inside a run as well as across runs.
The per-statistic rate counts every block of every seed.  The per-seed
table counts how many blocks of that seed pass all six statistics.

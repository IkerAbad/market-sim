# Block stability

Command:

```
python scripts/run_stability.py --config configs/baseline.json --results results --blocks 10
```

- Observations: 100000
- Blocks: 10
- Every statistic passes its criterion in every block: yes

| Block | Start | End | Kurtosis | ACF(returns, lag 1) | ACF(abs(returns), lag 1) | ACF(abs(returns), lag 50) | corr(volume, abs(returns)) | P(abs(r) > 4 sd) / P_normal |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 10000 | 4.521 | -0.01062 | 0.1415 | 0.1217 | 0.4959 | 36.31 |
| 2 | 10000 | 20000 | 4.141 | -0.002281 | 0.1281 | 0.08559 | 0.4875 | 17.37 |
| 3 | 20000 | 30000 | 7.773 | -0.02629 | 0.1952 | 0.1539 | 0.5505 | 59.99 |
| 4 | 30000 | 40000 | 4.436 | -0.001477 | 0.09989 | 0.07468 | 0.4786 | 14.21 |
| 5 | 40000 | 50000 | 4.361 | 0.02405 | 0.1144 | 0.08761 | 0.474 | 22.1 |
| 6 | 50000 | 60000 | 4.007 | -0.007423 | 0.1315 | 0.1075 | 0.4917 | 20.52 |
| 7 | 60000 | 70000 | 4.202 | 0.01184 | 0.1056 | 0.07436 | 0.4757 | 31.57 |
| 8 | 70000 | 80000 | 3.584 | -0.004683 | 0.07257 | 0.0577 | 0.3977 | 12.63 |
| 9 | 80000 | 90000 | 4.315 | -0.00163 | 0.1079 | 0.09456 | 0.4926 | 28.42 |
| 10 | 90000 | 100000 | 4.117 | -0.01723 | 0.1009 | 0.06738 | 0.4739 | 20.52 |

| Statistic | Mean | Min | Max | Blocks passing |
| --- | ---: | ---: | ---: | ---: |
| Kurtosis | 4.546 | 3.584 | 7.773 | 10/10 |
| ACF(returns, lag 1) | -0.003575 | -0.02629 | 0.02405 | 10/10 |
| ACF(abs(returns), lag 1) | 0.1198 | 0.07257 | 0.1952 | 10/10 |
| ACF(abs(returns), lag 50) | 0.0925 | 0.0577 | 0.1539 | 10/10 |
| corr(volume, abs(returns)) | 0.4818 | 0.3977 | 0.5505 | 10/10 |
| P(abs(r) > 4 sd) / P_normal | 26.36 | 12.63 | 59.99 | 10/10 |

## Reading

Each block is a contiguous slice of the same simulated series.  The
statistics are recomputed inside the block, so the table shows whether
the full-sample result comes from the whole window or from one episode.
Kurtosis is the least stable statistic because it is driven by the
largest returns.  The block table is descriptive and is not used as a
target fact.  The cross-seed version is in `docs/block_ensemble.md`.

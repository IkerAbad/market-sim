# Additional facts against the benchmarks

Command:

```
python scripts/run_additional_discrimination.py --config configs/baseline.json --seeds 1001-1020 --series 100 --n 100000 --jobs 8
```

- Model sample: 20 seeds
- GARCH and Gaussian samples: 100 series each
- Observations per series: 100000
- The volume lead-lag fact is omitted because the synthetic benchmarks
  have no volume.

| Additional fact | Model median | GARCH median | Gaussian median | AUC vs GARCH | AUC vs Gaussian |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leverage effect | 0.00426 | -0.0008269 | 0.0005386 | 0.298 | 0.352 |
| Gain/loss asymmetry | 0.9931 | 0.9992 | 0.9985 | 0.391 | 0.378 |
| DFA Hurst exponent | 0.8592 | 0.7378 | 0.5004 | 0.998 | 1.000 |
| Aggregational ratio | 0.7545 | 1.002 | 0.9977 | 0.804 | 0.840 |

## Reading

DFA Hurst separates the model from GARCH with AUC 0.998. Aggregational Gaussianity
separates them moderately, with AUC 0.804, because the model ratio is 0.754 and the
GARCH ratio is 1.002. Leverage does not separate them in the intended direction: AUC
0.298, and the model median is 0.00426 against -0.0008269 for GARCH. Gain/loss asymmetry
is close to a coin flip, with AUC 0.391 and both medians near 1. The additional facts
add the DFA exponent and aggregational Gaussianity to the discriminators. Leverage and
gain/loss do not help. The DFA exponent and ACF(abs, 50) are two views of the same slow
persistence, so the model's distinctive content is long memory.

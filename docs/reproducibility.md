# Reproducibility

## Reference environment

The committed numbers and figures were produced with:

- Windows 11
- Python 3.14.5
- NumPy 2.5.5
- Matplotlib 3.11.2

CI runs the tests on Ubuntu and Windows with Python 3.12, 3.13 and 3.14.  The
exact float values are tied to the reference environment because NumPy does not
promise bit-for-bit identical `Generator` streams across every version.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

On Linux or macOS use `source .venv/bin/activate` instead.

## Baseline

```bash
python scripts/run_simulation.py --config configs/baseline.json --output results
python scripts/make_figures.py --results results --output docs
```

This writes `results/series.csv` and the three figures.  The `results/`
directory is ignored by git.  The exact baseline summary is committed as
`docs/baseline_metrics.json`.

## Additional analyses

```bash
python scripts/run_ensemble.py --config configs/baseline.json --seeds 1001-1020 --jobs 8
python scripts/run_inference.py --config configs/baseline.json --results results --report docs/inference.md
python scripts/run_phase_diagram.py --config configs/baseline.json --seeds 1-3 --jobs 8
python scripts/run_extra_facts.py --results results --report docs/additional_facts.md
```

The ensemble and the phase map use a process pool.  The bootstrap uses 200
resamples of contiguous blocks of 1000 observations.  The phase map uses
30,000 steps per seed and three seeds per cell.  These are the settings used
for the committed reports.

## Tests and build

```bash
pytest --cov=market_sim --cov-report=term-missing --cov-fail-under=95
ruff check .
ruff format --check .
mypy src
python -m build
python -m twine check dist/*
```

The CI workflow runs the same gates.  It also runs the full 101,000-step
baseline, builds the three figures, runs a 3-seed ensemble smoke test and
installs the built wheel in a clean environment.

## Committed outputs

| File | SHA256 |
| --- | --- |
| `docs/price_series.png` | `8C9689D7CBD51476256DE9C8343435CA637F0FA88E581E9209B7D30185C31872` |
| `docs/return_histogram.png` | `C483B8175FC0CE54467482DB6E53BA833B80CF006926FF828B7681605DF7254B` |
| `docs/autocorrelation.png` | `20FF8947D2E674C83FFEA2DF9148DE6B5C0DE1DEA2D0E00D26BF52C906D68749` |
| `docs/phase_diagram.png` | `3FBB77D71FC4E9CBB4B24DEADA1637B1271291D690AC8815A66F3D8E478B7F71` |
| `docs/robustness.csv` | `9D485D761E597482BB161781BB640CB34C81C7171C583234EF2AA88633DCF664` |
| `docs/inference.csv` | `97B7205A955BE6AC2549E54EEEFF6223336814328F4A76D3B8EBEBE351EE3ED1` |
| `docs/additional_facts.csv` | `FFF87CB35D445038BFBBC8CD75885571D5FA9CDFD82BDD1797A0397127523BD6` |
| `docs/phase_diagram.csv` | `B8129AC6314E1B5FEA6E88F6B90521A70D374964241506D7C5F8E7ACBB6EF7E7` |
| `docs/baseline_metrics.json` | `31F33A81C8465CFC2606B8FF300A8151DF4421594CB7C936AA09A3C544020DE5` |

The three baseline figures are byte-identical when regenerated in the reference
environment.  The hash table is a check, not a substitute for the commands.

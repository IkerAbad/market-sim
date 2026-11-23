# Reproducibility

## Reference environment

The committed numbers and figures were produced with:

- Windows 11
- Python 3.14.5
- NumPy 2.5.5
- Matplotlib 3.11.2

CI runs the tests on Ubuntu and Windows with Python 3.12, 3.13 and 3.14.  The
exact float values are tied to the reference environment because NumPy does not
promise bit-for-bit identical `Generator` streams across every version.  The
reference versions are pinned in `constraints-reference.txt` and a CI job
installs that file before running the tests.

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
python scripts/run_ensemble.py --config configs/baseline.json --seeds 1001-1050 --jobs 8 --output results_ensemble_50 --report docs/robustness_50.md --csv-report docs/robustness_50.csv
python scripts/run_inference.py --config configs/baseline.json --results results --report docs/inference.md
python scripts/run_phase_diagram.py --config configs/baseline.json --seeds 1-3 --jobs 8
python scripts/run_ablations.py --config configs/baseline.json --seeds 1001-1003 --jobs 8
python scripts/run_sensitivity_full.py --config configs/baseline.json --seeds 1001-1003 --jobs 8
python scripts/run_thresholds.py --input docs/robustness.csv --report docs/thresholds.md
python scripts/run_extra_facts.py --results results --report docs/additional_facts.md
python scripts/run_benchmarks.py --config configs/baseline.json --results results --report docs/benchmarks.md
python scripts/run_benchmark.py --config configs/baseline.json --steps 10000,50000,100000
python scripts/run_sample_size.py --config configs/baseline.json --sizes 10000,50000,100000,200000 --seeds 1001-1003 --jobs 8
python scripts/run_price_volume.py --config configs/baseline.json --results results --report docs/price_volume.md
python scripts/run_stability.py --config configs/baseline.json --results results --blocks 10
```

To run every analysis in order:

```bash
python scripts/reproduce_all.py --jobs 8
```

The ensemble, phase map, ablation and sensitivity runners use a process pool.
The bootstrap uses 200 resamples of contiguous blocks of 1000 observations.
The phase map uses 30,000 steps per seed and three seeds per cell.  The
ablation and sensitivity runs use 101,000 steps and three seeds.  These are the
settings used for the committed reports.

`scripts/compare_real_data.py` is a separate tool for a user-supplied CSV.  It
is not part of the committed outputs because the data are not packaged.

## Container

```bash
docker build -t market-sim .
docker run --rm market-sim version
docker run --rm market-sim simulate --config configs/baseline.json --output /tmp/results
```

CI builds the image and runs a 500-step simulation inside it.

## Tests and build

```bash
pytest --cov=market_sim --cov-report=term-missing --cov-fail-under=98
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
| `docs/robustness_50.csv` | `E597B0FAE0051ADEBD2DC9BE8FE85765B124FAD443678627742E54A4C2C52702` |
| `docs/ablations.csv` | `C9E6EC1C3F1A6BA8BC4661851B276D3F4E68477F700281468DC8B5D00E7DE533` |
| `docs/sensitivity_full.csv` | `3F3D8AE751317CF422DDFE7139BFE87668DE8157A9ACFA03A1A760635DACE18B` |
| `docs/thresholds.csv` | `18F8BF5F55FBBF68D5605D04AA1D6AB25DBD30FFA0E60FB6A5EDC7D831E80153` |
| `docs/benchmarks.csv` | `4DD42A024FF55C7E24FCEFF9C8F994E6CEC622A4AE1D69C5AB1EE07FE0FA3E3B` |
| `docs/performance.csv` | `A1B4533529576001C410697F8ED15A5C37942C493E97603F3E44A58878265591` |
| `docs/sample_size.csv` | `F319DDDAB1ADC1B5E85359960C29B88D65FE2FDEE51877DC8EDE11669EDE57B8` |
| `docs/price_volume.csv` | `6948769BC613DEC23C717ED13BD6758376FD1D362848649F7DB374AF3FFB7602` |
| `docs/stability.csv` | `63766A0C0219BAB3BAB9E378480169C915D732581F2DE2CEFBADDDEC57245FF3` |
| `docs/baseline_metrics.json` | `31F33A81C8465CFC2606B8FF300A8151DF4421594CB7C936AA09A3C544020DE5` |

The three baseline figures are byte-identical when regenerated in the reference
environment.  The hash table is a check, not a substitute for the commands.

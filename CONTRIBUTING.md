# Contributing

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

On Linux or macOS use `source .venv/bin/activate` instead.

## Checks

Run the same gates as CI before opening a pull request:

```bash
ruff check .
ruff format --check .
mypy src
pytest --cov=market_sim --cov-report=term-missing --cov-fail-under=95
python -m build
```

## Reproducibility

- Do not change the baseline seed without regenerating `results/` and the
  figures in `docs/`.
- If a model parameter changes, rerun the single-seed table, the sensitivity
  runs and the seed ensemble.
- Every number in the README must be traceable to a command in the README or
  in `docs/`.

## Pull requests

Keep changes focused. Add or update tests for behaviour changes. CI runs on
Ubuntu and Windows with Python 3.12, 3.13 and 3.14.

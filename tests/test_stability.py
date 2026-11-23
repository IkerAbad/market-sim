from __future__ import annotations

import numpy as np
import pytest

from market_sim.config import MetricsParams
from market_sim.stability import (
    CRITERIA,
    METRIC_KEYS,
    block_metrics,
    block_passes,
    format_stability_markdown,
    summarize_blocks,
    write_stability_csv,
)

PARAMS = MetricsParams(acf_lags=50)


def _series(n: int = 5000, seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    returns = rng.standard_t(df=4, size=n) * 0.01
    volume = np.abs(rng.standard_normal(n)) + 0.1
    return returns, volume


def test_block_metrics_covers_the_whole_series() -> None:
    returns, volume = _series()
    blocks = block_metrics(returns, volume, PARAMS, n_blocks=5)
    assert len(blocks) == 5
    assert blocks[0].start == 0
    assert blocks[-1].end == len(returns)
    assert sum(block.n_observations for block in blocks) == len(returns)
    for block in blocks:
        assert set(block.metrics) == set(METRIC_KEYS)


def test_block_metrics_rejects_bad_input() -> None:
    returns, volume = _series(200)
    with pytest.raises(ValueError):
        block_metrics(returns, volume, PARAMS, n_blocks=1)
    with pytest.raises(ValueError):
        block_metrics(returns[:-1], volume, PARAMS, n_blocks=2)
    with pytest.raises(ValueError):
        block_metrics(returns, volume, PARAMS, n_blocks=10)
    bad = returns.copy()
    bad[0] = np.nan
    with pytest.raises(ValueError):
        block_metrics(bad, volume, PARAMS, n_blocks=2)


def test_summary_counts_block_passes() -> None:
    returns, volume = _series()
    blocks = block_metrics(returns, volume, PARAMS, n_blocks=5)
    summary = summarize_blocks(blocks, PARAMS)
    for key in METRIC_KEYS:
        row = summary[key]
        assert row["total"] == 5
        assert 0 <= row["passes"] <= 5
        assert row["min"] <= row["mean"] <= row["max"]


def test_undefined_metric_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    returns, volume = _series(200)
    monkeypatch.setattr(
        "market_sim.stability.compute_metrics",
        lambda *args, **kwargs: {key: None for key in METRIC_KEYS},
    )
    with pytest.raises(ValueError):
        block_metrics(returns, volume, PARAMS, n_blocks=2)


def test_summarize_empty_blocks_is_rejected() -> None:
    with pytest.raises(ValueError):
        summarize_blocks([], PARAMS)


def test_block_passes_directions() -> None:
    assert block_passes("kurtosis", 4.0, PARAMS)
    assert not block_passes("kurtosis", 2.0, PARAMS)
    assert block_passes("acf_return_lag1", -0.01, PARAMS)
    assert not block_passes("acf_return_lag1", 0.2, PARAMS)
    with pytest.raises(ValueError):
        block_passes("unknown", 0.0, PARAMS)


def test_unknown_direction_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(CRITERIA, "kurtosis", ("sideways", "kurtosis_threshold"))
    with pytest.raises(ValueError):
        block_passes("kurtosis", 4.0, PARAMS)


def test_markdown_contains_every_block() -> None:
    returns, volume = _series()
    blocks = block_metrics(returns, volume, PARAMS, n_blocks=4)
    markdown = format_stability_markdown(blocks, PARAMS)
    assert "| Block | Start | End |" in markdown
    assert "Blocks passing" in markdown
    for block in blocks:
        assert f"| {block.index} | {block.start} | {block.end} |" in markdown


def test_csv_has_one_row_per_block(tmp_path) -> None:
    returns, volume = _series()
    blocks = block_metrics(returns, volume, PARAMS, n_blocks=3)
    path = write_stability_csv(blocks, tmp_path / "stability.csv")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 4
    assert lines[0].startswith("block,start,end,n_observations")

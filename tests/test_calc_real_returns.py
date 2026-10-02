"""Tests for the real-return block bootstrap calculator."""

import csv
import json
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_real_returns import (  # noqa: E402
    AnnualReturn,
    Config,
    PortfolioWeights,
    load_real_portfolio_returns,
    portfolio_weights_from_percentages,
    rolling_blocks,
    run,
)


def write_real_return_csv(path: Path) -> None:
    rows = [
        ["Annual Returns on Investments in"],
        [
            "Year",
            "S&P 500 (includes dividends)2",
            "3-month T. Bill (Real)",
            "Baa Corp Bonds",
            "Gold",
        ],
        ["2000", "10%", "1%", "2%", "3%"],
        ["2001", "0%", "2%", "3%", "4%"],
        ["2002", "-10%", "3%", "4%", "5%"],
        ["2003", "20%", "4%", "5%", "6%"],
        ["2004", "5%", "5%", "6%", "7%"],
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        csv.writer(file).writerows(rows)


def test_loads_precomputed_real_component_returns_and_weights_them(tmp_path: Path) -> None:
    csv_path = tmp_path / "returns.csv"
    write_real_return_csv(csv_path)

    returns = load_real_portfolio_returns(
        csv_path, portfolio_weights_from_percentages(70, 10, 10, 10)
    )

    assert [annual_return.year for annual_return in returns] == [2000, 2001, 2002, 2003, 2004]
    assert returns[0].sp500_return == pytest.approx(0.10)
    assert returns[0].tbills_return == pytest.approx(0.01)
    assert returns[0].return_rate == pytest.approx(0.076)


def test_rejects_portfolio_percentages_that_do_not_total_100() -> None:
    with pytest.raises(ValueError, match="must sum to 100"):
        portfolio_weights_from_percentages(72, 3, 15, 9)

    with pytest.raises(ValueError, match="cannot be negative"):
        portfolio_weights_from_percentages(72, -3, 15, 16)


def test_rolling_blocks_exclude_sequences_with_missing_years() -> None:
    returns = [
        AnnualReturn(year, 0, 0, 0, 0, 0)
        for year in (2000, 2001, 2003, 2004)
    ]

    blocks = rolling_blocks(returns, first_year=2000, block_years=2)

    assert [block.start_year for block in blocks] == [2000, 2003]


def test_run_enumerates_ordered_block_pairs_and_writes_summary(tmp_path: Path) -> None:
    csv_path = tmp_path / "returns.csv"
    output_dir = tmp_path / "output"
    write_real_return_csv(csv_path)

    summary = run(
        csv_path,
        output_dir,
        PortfolioWeights(sp500=1, tbills=0, corp_bonds=0, gold=0),
        Config(first_block_year=2000, block_years=2, path_years=4),
    )

    assert summary["rolling_block_count"] == 4
    assert summary["ordered_path_count"] == 16
    assert summary["real_cagr_distribution"]["minimum"] == pytest.approx(
        math.pow(0.9 * 0.9, 0.25) - 1
    )
    assert summary["real_cagr_distribution"]["maximum"] == pytest.approx(
        math.pow(1.2 * 1.05 * 1.2 * 1.05, 0.25) - 1
    )
    assert (output_dir / "path_summary.csv").is_file()
    assert (output_dir / "annual_detail.csv").is_file()
    assert json.loads((output_dir / "summary.json").read_text()) == summary

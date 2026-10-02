#!/usr/bin/env python3
"""Calculate real portfolio returns with the CLAT calculator's block bootstrap.

The default portfolio is 72% S&P 500, 3% 3-month Treasury bills, 15% Baa
corporate bonds, and 10% gold. The default data path is the historical CSV used
by ``clat_gold_bootstrap.py``. Pass all desired allocation flags as whole
percentages; when any allocation is supplied, omitted allocations are 0%.

Example:
  python calc_real_returns.py --sp500 72 --corp-bonds 15 --tbils 3 --gold 10

The calculation creates every contiguous 10-year block from 1970 onward, then
evaluates every ordered pair of blocks as a synthetic 20-year path. It reports
the distribution of real compound annual growth rates and ending values for a
$1 starting investment.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable


DEFAULT_CSV_PATH = Path("/Users/eric/Documents/FinanceData/Block Finance 10 Year - Data.csv")


@dataclass(frozen=True)
class Config:
    first_block_year: int = 1970
    block_years: int = 10
    path_years: int = 20


@dataclass(frozen=True)
class PortfolioWeights:
    sp500: float
    tbills: float
    corp_bonds: float
    gold: float

    def as_percentages(self) -> dict[str, float]:
        return {name: value * 100 for name, value in asdict(self).items()}


@dataclass(frozen=True)
class AnnualReturn:
    year: int
    return_rate: float
    sp500_return: float
    tbills_return: float
    corp_bonds_return: float
    gold_return: float


@dataclass(frozen=True)
class Block:
    start_year: int
    returns: tuple[AnnualReturn, ...]

    @property
    def end_year(self) -> int:
        return self.returns[-1].year


def parse_percent(value: str) -> float:
    """Turn values such as '12.34%' or '-0.15%' into decimal returns."""
    cleaned = value.strip().replace(",", "")
    if not cleaned or cleaned.upper() in {"N/A", "NA"}:
        raise ValueError("blank or non-numeric return")
    if cleaned.endswith("%"):
        return float(cleaned[:-1]) / 100.0
    number = float(cleaned)
    return number / 100.0 if abs(number) > 1 else number


def portfolio_weights_from_percentages(
    sp500: float, tbills: float, corp_bonds: float, gold: float
) -> PortfolioWeights:
    """Validate whole-percentage weights and convert them to decimal weights."""
    percentages = {
        "sp500": sp500,
        "tbills": tbills,
        "corp_bonds": corp_bonds,
        "gold": gold,
    }
    if any(value < 0 for value in percentages.values()):
        raise ValueError("Portfolio percentages cannot be negative.")
    total = sum(percentages.values())
    if not math.isclose(total, 100.0, abs_tol=1e-9):
        raise ValueError(f"Portfolio percentages must sum to 100; received {total:.12f}.")
    return PortfolioWeights(**{name: value / 100.0 for name, value in percentages.items()})


def find_header_and_real_return_columns(rows: list[list[str]]) -> tuple[int, dict[str, int]]:
    """Find the historical table header and four real-return component columns."""
    expected_columns = {
        "sp500": "s&p 500 (includes dividends)2",
        "tbills": "3-month t. bill (real)",
        "corp_bonds": "baa corp bonds",
        "gold": "gold",
    }
    for row_index, row in enumerate(rows):
        normalized = [cell.strip().lower() for cell in row]
        if "year" not in normalized:
            continue
        column_indexes = {}
        for name, expected_label in expected_columns.items():
            try:
                column_indexes[name] = normalized.index(expected_label)
            except ValueError:
                break
        if len(column_indexes) == len(expected_columns):
            return row_index, column_indexes
    raise ValueError(
        "Could not find the real S&P 500, 3-month T.Bill, Baa Corporate Bond, "
        "and Gold columns required by the portfolio."
    )


def load_real_portfolio_returns(
    csv_path: Path, weights: PortfolioWeights
) -> list[AnnualReturn]:
    """Load and weight the historical table's precomputed real-return columns."""
    with csv_path.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.reader(file))
    header_index, column_indexes = find_header_and_real_return_columns(rows)
    year_index = next(
        index
        for index, cell in enumerate(rows[header_index])
        if cell.strip().lower() == "year"
    )

    returns: list[AnnualReturn] = []
    for row in rows[header_index + 1 :]:
        if len(row) <= max(year_index, *column_indexes.values()):
            continue
        try:
            year = int(row[year_index].strip())
            components = {
                name: parse_percent(row[column_index])
                for name, column_index in column_indexes.items()
            }
        except ValueError:
            continue
        returns.append(
            AnnualReturn(
                year=year,
                return_rate=sum(
                    getattr(weights, name) * components[name] for name in column_indexes
                ),
                sp500_return=components["sp500"],
                tbills_return=components["tbills"],
                corp_bonds_return=components["corp_bonds"],
                gold_return=components["gold"],
            )
        )

    if not returns:
        raise ValueError("No usable annual real portfolio returns were found.")
    returns.sort(key=lambda item: item.year)
    if len({item.year for item in returns}) != len(returns):
        raise ValueError("The input contains duplicate years.")
    return returns


def rolling_blocks(
    returns: list[AnnualReturn], first_year: int, block_years: int
) -> list[Block]:
    """Create every contiguous rolling block beginning at or after ``first_year``."""
    eligible = [item for item in returns if item.year >= first_year]
    blocks: list[Block] = []
    for index in range(len(eligible) - block_years + 1):
        candidate = eligible[index : index + block_years]
        if all(
            candidate[offset].year == candidate[0].year + offset
            for offset in range(block_years)
        ):
            blocks.append(Block(candidate[0].year, tuple(candidate)))
    if not blocks:
        raise ValueError(
            f"No contiguous {block_years}-year blocks beginning in {first_year} were found."
        )
    return blocks


def cagr(annual_returns: Iterable[AnnualReturn]) -> float:
    """Calculate compound annual growth from annual real portfolio returns."""
    returns = tuple(annual_returns)
    if not returns:
        raise ValueError("Cannot calculate a CAGR for an empty sequence.")
    gross_return = math.prod(1 + item.return_rate for item in returns)
    return gross_return ** (1 / len(returns)) - 1


def percentile(values: list[float], requested_percentile: float) -> float:
    """Calculate a linearly interpolated percentile."""
    if not values:
        raise ValueError("Cannot calculate a percentile for no values.")
    ordered = sorted(values)
    position = (len(ordered) - 1) * requested_percentile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def simulate_path(block_one: Block, block_two: Block, config: Config) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Calculate one ordered two-block path and its annual real-return details."""
    sequence = block_one.returns + block_two.returns
    if len(sequence) != config.path_years:
        raise AssertionError("Each bootstrap path must have exactly one return per path year.")

    ending_value = math.prod(1 + item.return_rate for item in sequence)
    path_id = f"{block_one.start_year}_{block_two.start_year}"
    path = {
        "path_id": path_id,
        "block_one_start_year": block_one.start_year,
        "block_one_end_year": block_one.end_year,
        "block_two_start_year": block_two.start_year,
        "block_two_end_year": block_two.end_year,
        "real_portfolio_cagr": cagr(sequence),
        "ending_value_of_one": ending_value,
    }
    annual_rows = [
        {
            "path_id": path_id,
            "path_year": path_year,
            "historical_year": annual_return.year,
            "sp500_real_return": annual_return.sp500_return,
            "tbills_real_return": annual_return.tbills_return,
            "corp_bonds_real_return": annual_return.corp_bonds_return,
            "gold_real_return": annual_return.gold_return,
            "real_portfolio_return": annual_return.return_rate,
        }
        for path_year, annual_return in enumerate(sequence, start=1)
    ]
    return path, annual_rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def distribution(values: list[float]) -> dict[str, float]:
    """Return the distribution statistics used in the bootstrap summary."""
    return {
        "p10": percentile(values, 0.10),
        "p25": percentile(values, 0.25),
        "median": percentile(values, 0.50),
        "p75": percentile(values, 0.75),
        "p90": percentile(values, 0.90),
        "mean": mean(values),
        "minimum": min(values),
        "maximum": max(values),
    }


def run(
    csv_path: Path,
    output_dir: Path,
    weights: PortfolioWeights,
    config: Config = Config(),
) -> dict[str, object]:
    """Run the exhaustive paired-block bootstrap and write its results."""
    if config.path_years != 2 * config.block_years:
        raise ValueError("This paired-block bootstrap requires path_years to equal two blocks.")

    returns = load_real_portfolio_returns(csv_path, weights)
    blocks = rolling_blocks(returns, config.first_block_year, config.block_years)
    paths: list[dict[str, object]] = []
    annual_rows: list[dict[str, object]] = []
    for block_one in blocks:
        for block_two in blocks:
            path, annual = simulate_path(block_one, block_two, config)
            paths.append(path)
            annual_rows.extend(annual)

    cagrs = [float(path["real_portfolio_cagr"]) for path in paths]
    ending_values = [float(path["ending_value_of_one"]) for path in paths]
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "input_csv": str(csv_path.resolve()),
        "config": asdict(config),
        "portfolio_weights_percent": weights.as_percentages(),
        "annual_return_years_loaded": [returns[0].year, returns[-1].year],
        "rolling_block_count": len(blocks),
        "ordered_path_count": len(paths),
        "real_cagr_distribution": distribution(cagrs),
        "ending_value_of_one_distribution": distribution(ending_values),
        "files": {
            "path_summary": "path_summary.csv",
            "annual_detail": "annual_detail.csv",
        },
    }
    write_csv(output_dir / "path_summary.csv", paths)
    write_csv(output_dir / "annual_detail.csv", annual_rows)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
    return summary


def resolve_portfolio_weights(arguments: argparse.Namespace) -> PortfolioWeights:
    """Apply defaults only when no allocation flags were provided."""
    supplied_weights = [
        arguments.sp500,
        arguments.tbills,
        arguments.corp_bonds,
        arguments.gold,
    ]
    if all(value is None for value in supplied_weights):
        return portfolio_weights_from_percentages(72, 3, 15, 10)
    return portfolio_weights_from_percentages(
        arguments.sp500 or 0,
        arguments.tbills or 0,
        arguments.corp_bonds or 0,
        arguments.gold or 0,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"Historical CSV source (default: {DEFAULT_CSV_PATH})",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("real_returns_output"))
    parser.add_argument("--sp500", type=float, help="S&P 500 allocation as a percentage")
    parser.add_argument(
        "--tbils",
        "--tbills",
        "--cash",
        dest="tbills",
        type=float,
        help="3-month Treasury-bill allocation as a percentage",
    )
    parser.add_argument(
        "--corp-bonds", dest="corp_bonds", type=float, help="Baa corporate-bond allocation as a percentage"
    )
    parser.add_argument("--gold", type=float, help="Gold allocation as a percentage")
    arguments = parser.parse_args()
    try:
        weights = resolve_portfolio_weights(arguments)
        summary = run(arguments.data, arguments.output_dir, weights)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

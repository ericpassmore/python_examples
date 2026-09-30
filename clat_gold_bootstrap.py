#!/usr/bin/env python3
"""Bootstrap a 20-year grantor CLAT using annual nominal portfolio returns.

The input CSV is expected to contain the historical table supplied with this
analysis.  It may include title rows before the header; the parser locates the
row containing ``Year`` and the required nominal portfolio-return columns
automatically.

Examples:
  python clat_gold_bootstrap.py \
      "/Users/eric/Downloads/Block Finance 10 Year - Data.csv"
  python clat_gold_bootstrap.py data.csv --schedule flat --output-dir flat_run

The default portfolio is 72% S&P 500, 3% 3-month Treasury bills (cash), 15%
Baa corporate bonds, and 10% gold. The default ``shark_fin`` schedule grows
each requested charitable payment by 22% annually. ``flat`` makes each
requested payment equal. In either case, the first payment is independently
solved so the charitable interest has a $1,000,000 present value at the
specified Section 7520 rate.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median
from typing import Iterable


@dataclass(frozen=True)
class Config:
    # Core CLAT assumptions.  Change these values to model another trust.
    initial_clat: float = 1_000_000.0
    term_years: int = 20
    section_7520_rate: float = 0.056
    shark_fin_growth: float = 0.22
    first_block_year: int = 1970
    # Annual portfolio weights. They must sum to 100%.
    sp500_weight: float = 0.72
    cash_weight: float = 0.03
    baa_corporate_bond_weight: float = 0.15
    gold_weight: float = 0.10
    # "Similar CAGR" groups use one-percentage-point-wide bins by default.
    cagr_bin_width: float = 0.01


@dataclass(frozen=True)
class AnnualReturn:
    year: int
    return_rate: float
    sp500_return: float
    cash_return: float
    baa_corporate_bond_return: float
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
    # The supplied table expresses returns as percentages.  This fallback also
    # accepts decimal-form inputs without changing percent-form inputs.
    number = float(cleaned)
    return number / 100.0 if abs(number) > 1 else number


def find_header_and_portfolio_columns(rows: list[list[str]]) -> tuple[int, dict[str, int]]:
    """Find the header and the four nominal return columns used by the portfolio."""
    expected_columns = {
        "sp500": "s&p 500 (includes dividends)",
        "cash": "3-month t.bill",
        "baa_corporate_bond": "baa corporate bond",
        "gold": "gold*",
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
        "Could not find the nominal S&P 500, 3-month T.Bill, Baa Corporate Bond, "
        "and Gold* columns required by the portfolio."
    )


def load_nominal_portfolio_returns(csv_path: Path, config: Config) -> list[AnnualReturn]:
    weights = {
        "sp500": config.sp500_weight,
        "cash": config.cash_weight,
        "baa_corporate_bond": config.baa_corporate_bond_weight,
        "gold": config.gold_weight,
    }
    if not math.isclose(sum(weights.values()), 1.0, abs_tol=1e-12):
        raise ValueError(f"Portfolio weights must sum to 1.0; received {sum(weights.values()):.12f}.")
    with csv_path.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.reader(file))
    header_index, column_indexes = find_header_and_portfolio_columns(rows)
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
                return_rate=sum(weights[name] * components[name] for name in weights),
                sp500_return=components["sp500"],
                cash_return=components["cash"],
                baa_corporate_bond_return=components["baa_corporate_bond"],
                gold_return=components["gold"],
            )
        )
    if not returns:
        raise ValueError("No usable annual nominal portfolio returns were found.")
    returns.sort(key=lambda item: item.year)
    if len({item.year for item in returns}) != len(returns):
        raise ValueError("The input contains duplicate years.")
    return returns


def rolling_blocks(
    returns: list[AnnualReturn], first_year: int, block_years: int
) -> list[Block]:
    """Create every contiguous, rolling block beginning at or after first_year."""
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


def first_payment(config: Config, schedule: str) -> float:
    growth = config.shark_fin_growth if schedule == "shark_fin" else 0.0
    present_value_factor = sum(
        (1 + growth) ** year / (1 + config.section_7520_rate) ** (year + 1)
        for year in range(config.term_years)
    )
    return config.initial_clat / present_value_factor


def cagr(annual_returns: Iterable[AnnualReturn]) -> float:
    returns = tuple(annual_returns)
    gross_return = math.prod(1 + item.return_rate for item in returns)
    return gross_return ** (1 / len(returns)) - 1


def simulate_path(
    block_one: Block, block_two: Block, config: Config, schedule: str
) -> tuple[dict[str, object], list[dict[str, object]]]:
    sequence = block_one.returns + block_two.returns
    if len(sequence) != config.term_years:
        raise AssertionError("Each bootstrap path must have exactly one return per CLAT year.")
    payment_one = first_payment(config, schedule)
    growth = config.shark_fin_growth if schedule == "shark_fin" else 0.0
    balance = config.initial_clat
    exhausted = False
    exhaustion_year: int | None = None
    annual_rows: list[dict[str, object]] = []

    for trust_year, annual_return in enumerate(sequence, start=1):
        requested_payment = payment_one * (1 + growth) ** (trust_year - 1)
        beginning_balance = balance
        investment_gain_loss = beginning_balance * annual_return.return_rate
        balance_after_return = max(0.0, beginning_balance + investment_gain_loss)
        payment_paid = min(balance_after_return, requested_payment)
        unpaid_payment = requested_payment - payment_paid
        balance = max(0.0, balance_after_return - payment_paid)
        if unpaid_payment > 0.005 and not exhausted:
            exhausted = True
            exhaustion_year = trust_year

        annual_rows.append(
            {
                "path_id": f"{block_one.start_year}_{block_two.start_year}",
                "block_one_start_year": block_one.start_year,
                "block_two_start_year": block_two.start_year,
                "trust_year": trust_year,
                "historical_year": annual_return.year,
                "beginning_balance": beginning_balance,
                "sp500_return": annual_return.sp500_return,
                "cash_return": annual_return.cash_return,
                "baa_corporate_bond_return": annual_return.baa_corporate_bond_return,
                "gold_return": annual_return.gold_return,
                "nominal_portfolio_return": annual_return.return_rate,
                "investment_gain_loss": investment_gain_loss,
                "scheduled_charitable_payment": requested_payment,
                "charitable_payment_paid": payment_paid,
                "unpaid_charitable_payment": unpaid_payment,
                "ending_balance": balance,
                "exhausted": exhausted,
                "exhaustion_year": exhaustion_year or "",
            }
        )

    path = {
        "path_id": f"{block_one.start_year}_{block_two.start_year}",
        "block_one_start_year": block_one.start_year,
        "block_one_end_year": block_one.end_year,
        "block_two_start_year": block_two.start_year,
        "block_two_end_year": block_two.end_year,
        "twenty_year_cagr": cagr(sequence),
        "exhausted": exhausted,
        "exhaustion_year": exhaustion_year or "",
        "final_remainder": 0.0 if exhausted else balance,
    }
    return path, annual_rows


def percentile(values: list[float], requested_percentile: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile for no values.")
    ordered = sorted(values)
    position = (len(ordered) - 1) * requested_percentile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def cagr_bin(value: float, width: float) -> float:
    return math.floor(value / width) * width


def build_cagr_bin_comparisons(paths: list[dict[str, object]], width: float) -> list[dict[str, object]]:
    grouped: dict[float, list[dict[str, object]]] = {}
    for path in paths:
        grouped.setdefault(cagr_bin(float(path["twenty_year_cagr"]), width), []).append(path)
    comparisons = []
    for lower_bound, members in sorted(grouped.items()):
        if len(members) < 2:
            continue
        remainders = [float(member["final_remainder"]) for member in members]
        comparisons.append(
            {
                "cagr_lower_bound": lower_bound,
                "cagr_upper_bound": lower_bound + width,
                "path_count": len(members),
                "exhaustion_rate": sum(bool(member["exhausted"]) for member in members) / len(members),
                "minimum_remainder": min(remainders),
                "median_remainder": median(remainders),
                "maximum_remainder": max(remainders),
                "remainder_spread": max(remainders) - min(remainders),
            }
        )
    return comparisons


def build_order_reversal_comparisons(paths: list[dict[str, object]]) -> list[dict[str, object]]:
    """Compare A→B versus B→A: same annual factors/CAGR, different ordering."""
    by_pair = {
        (int(path["block_one_start_year"]), int(path["block_two_start_year"])): path
        for path in paths
    }
    comparisons: list[dict[str, object]] = []
    for (first_start, second_start), forward in sorted(by_pair.items()):
        if first_start >= second_start:
            continue
        reverse = by_pair[(second_start, first_start)]
        forward_remainder = float(forward["final_remainder"])
        reverse_remainder = float(reverse["final_remainder"])
        comparisons.append(
            {
                "forward_path": forward["path_id"],
                "reverse_path": reverse["path_id"],
                "twenty_year_cagr": forward["twenty_year_cagr"],
                "forward_final_remainder": forward_remainder,
                "reverse_final_remainder": reverse_remainder,
                "remainder_difference_forward_minus_reverse": forward_remainder - reverse_remainder,
                "forward_exhausted": forward["exhausted"],
                "reverse_exhausted": reverse["exhausted"],
                "different_sequence_result": (
                    bool(forward["exhausted"]) != bool(reverse["exhausted"])
                    or abs(forward_remainder - reverse_remainder) > 0.005
                ),
            }
        )
    return comparisons


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(csv_path: Path, output_dir: Path, schedule: str, config: Config) -> dict[str, object]:
    returns = load_nominal_portfolio_returns(csv_path, config)
    block_years = config.term_years // 2
    if config.term_years % 2:
        raise ValueError("This two-block bootstrap requires an even CLAT term.")
    blocks = rolling_blocks(returns, config.first_block_year, block_years)
    paths: list[dict[str, object]] = []
    annual_rows: list[dict[str, object]] = []
    for block_one in blocks:
        for block_two in blocks:
            path, annual = simulate_path(block_one, block_two, config, schedule)
            paths.append(path)
            annual_rows.extend(annual)

    remainders = [float(path["final_remainder"]) for path in paths]
    exhausted_count = sum(bool(path["exhausted"]) for path in paths)
    output_dir.mkdir(parents=True, exist_ok=True)
    cagr_comparisons = build_cagr_bin_comparisons(paths, config.cagr_bin_width)
    order_comparisons = build_order_reversal_comparisons(paths)
    summary = {
        "input_csv": str(csv_path.resolve()),
        "schedule": schedule,
        "config": asdict(config),
        "portfolio_weights": {
            "sp500": config.sp500_weight,
            "cash": config.cash_weight,
            "baa_corporate_bond": config.baa_corporate_bond_weight,
            "gold": config.gold_weight,
        },
        "first_year_payment": first_payment(config, schedule),
        "nominal_total_scheduled_charitable_payments": first_payment(config, schedule)
        * sum((1 + (config.shark_fin_growth if schedule == "shark_fin" else 0.0)) ** year for year in range(config.term_years)),
        "annual_return_years_loaded": [returns[0].year, returns[-1].year],
        "rolling_ten_year_blocks": len(blocks),
        "ordered_twenty_year_paths": len(paths),
        "exhausted_paths": exhausted_count,
        "exhaustion_rate": exhausted_count / len(paths),
        "remainder_percentiles": {
            "p10": percentile(remainders, 0.10),
            "p25": percentile(remainders, 0.25),
            "median": percentile(remainders, 0.50),
            "p75": percentile(remainders, 0.75),
            "p90": percentile(remainders, 0.90),
        },
        "mean_remainder": mean(remainders),
        "minimum_remainder": min(remainders),
        "maximum_remainder": max(remainders),
        "same_cagr_order_reversal_pairs": len(order_comparisons),
        "order_reversal_pairs_with_different_sequence_results": sum(
            bool(row["different_sequence_result"]) for row in order_comparisons
        ),
        "files": {
            "path_summary": "path_summary.csv",
            "annual_detail": "annual_detail.csv",
            "similar_cagr_comparisons": "similar_cagr_comparisons.csv",
            "order_reversal_comparisons": "order_reversal_comparisons.csv",
        },
    }
    write_csv(output_dir / "path_summary.csv", paths)
    write_csv(output_dir / "annual_detail.csv", annual_rows)
    write_csv(output_dir / "similar_cagr_comparisons.csv", cagr_comparisons)
    write_csv(output_dir / "order_reversal_comparisons.csv", order_comparisons)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path", type=Path,
        help="CSV containing annual nominal S&P 500, cash, Baa corporate bond, and gold returns",
    )
    parser.add_argument(
        "--schedule", choices=("shark_fin", "flat"), default="shark_fin",
        help="Payment schedule; shark_fin is the default.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("clat_output"))
    arguments = parser.parse_args()
    summary = run(arguments.csv_path, arguments.output_dir, arguments.schedule, Config())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

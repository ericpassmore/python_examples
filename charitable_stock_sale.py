#!/usr/bin/env python3
"""Compare a taxable long-term stock sale with an in-kind stock gift.

This is a high-income federal tax illustration, not tax advice or a tax-return
preparation tool. It models tax year 2026 for taxpayers married filing jointly
whose only income is the modeled long-term capital gain. Change the grouped
constants below if a different tax year or assumption is needed.

Example:
    python3 charitable_stock_sale.py \
        --total-shares 100000 \
        --cost-basis-per-share 100 \
        --sale-price-per-share 500 \
        --charitable-contribution 10000000

Automatic donation-optimization example:
    python3 charitable_stock_sale.py \
        --total-shares 100000 \
        --cost-basis-per-share 100 \
        --sale-price-per-share 500 \
        --maximize-tax-savings-percentage

Assumptions: a qualifying public charity receives appreciated shares before
the taxpayer sells the remaining shares; all shares have the supplied average
basis and produce long-term gain; there is no other income, deduction, credit,
state tax, capital-loss offset, or prior charitable carryforward. The program
does not prepare Form 8283 or a tax return.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation, ROUND_FLOOR, ROUND_HALF_UP
from typing import Sequence


# Tax year 2026 federal assumptions for a married couple filing jointly.
# Keep these together so a future tax-year update is straightforward.
TAX_YEAR = 2026
LTCG_RATE = Decimal("0.20")
NIIT_RATE = Decimal("0.038")
NIIT_MFJ_THRESHOLD = Decimal("250000")
CHARITABLE_FLOOR_RATE = Decimal("0.005")
APPRECIATED_STOCK_PUBLIC_CHARITY_LIMIT_RATE = Decimal("0.30")
SECTION_68_REDUCTION_RATE = Decimal(2) / Decimal(37)
SECTION_68_MFJ_THRESHOLD = Decimal("768700")

ZERO = Decimal("0")
CENT = Decimal("0.01")


class InputValidationError(ValueError):
    """Raised when CLI values cannot describe the modeled stock sale."""


@dataclass(frozen=True)
class SaleInputs:
    """Inputs shared by the two sale scenarios."""

    total_shares: int
    cost_basis_per_share: Decimal
    sale_price_per_share: Decimal
    requested_charitable_contribution: Decimal


@dataclass(frozen=True)
class ScenarioResult:
    """Calculated sale, deduction, and federal-tax amounts for one scenario."""

    label: str
    donated_shares: int
    donation_value: Decimal
    shares_sold: int
    gross_proceeds: Decimal
    sold_share_cost_basis: Decimal
    realized_long_term_gain: Decimal
    agi: Decimal
    contribution_percentage_limit: Decimal
    contribution_subject_to_limit: Decimal
    charitable_floor: Decimal
    floor_disallowed: Decimal
    percentage_limit_excess: Decimal
    potential_carryforward: Decimal
    deduction_before_section_68: Decimal
    taxable_income_before_section_68: Decimal
    section_68_income_excess: Decimal
    section_68_reduction: Decimal
    allowed_charitable_deduction: Decimal
    ltcg_tax_before_deduction: Decimal
    charitable_deduction_tax_benefit: Decimal
    ltcg_tax_after_deduction: Decimal
    niit_tax_base: Decimal
    niit: Decimal
    total_federal_tax: Decimal
    liquid_net_after_tax: Decimal


@dataclass(frozen=True)
class ComparisonResult:
    """Both alternatives and the whole-share in-kind gift conversion."""

    requested_contribution: Decimal
    donation_shares: int
    actual_donation_value: Decimal
    no_contribution: ScenarioResult
    in_kind_donation: ScenarioResult


@dataclass(frozen=True)
class DonationOptimizationResult:
    """The donation with the best deduction-only tax-benefit percentage."""

    initial_gross_proceeds: Decimal
    gross_sales_ceiling: Decimal
    maximum_donation_shares: int
    selected_donation_shares: int
    selected_donation_value: Decimal
    charitable_deduction_tax_benefit: Decimal
    tax_savings_percentage: Decimal
    comparison: ComparisonResult


def parse_decimal(value: str) -> Decimal:
    """Parse a finite decimal without accepting float rounding artifacts."""

    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError(f"must be a number: {value!r}") from error
    if not parsed.is_finite():
        raise argparse.ArgumentTypeError("must be a finite number")
    return parsed


def parse_positive_whole_shares(value: str) -> int:
    """Parse the total share count as a positive whole number."""

    parsed = parse_decimal(value)
    if parsed <= ZERO or parsed != parsed.to_integral_value():
        raise argparse.ArgumentTypeError("must be a positive whole number")
    return int(parsed)


def parse_nonnegative_decimal(value: str) -> Decimal:
    """Parse a nonnegative monetary input."""

    parsed = parse_decimal(value)
    if parsed < ZERO:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def parse_positive_decimal(value: str) -> Decimal:
    """Parse a strictly positive monetary input."""

    parsed = parse_decimal(value)
    if parsed <= ZERO:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def whole_donation_shares(requested_dollars: Decimal, sale_price: Decimal) -> int:
    """Convert a requested gift amount to whole shares, always rounding down."""

    return int((requested_dollars / sale_price).to_integral_value(rounding=ROUND_FLOOR))


def validate_inputs(inputs: SaleInputs) -> None:
    """Reject values outside this simplified long-term-gain model."""

    if inputs.total_shares <= 0:
        raise InputValidationError("total shares must be a positive whole number")
    if inputs.cost_basis_per_share < ZERO:
        raise InputValidationError("cost basis per share must be zero or greater")
    if inputs.sale_price_per_share <= ZERO:
        raise InputValidationError("sale price per share must be greater than zero")
    if inputs.sale_price_per_share <= inputs.cost_basis_per_share:
        raise InputValidationError(
            "sale price per share must exceed cost basis per share for this "
            "long-term-gain illustration"
        )
    if inputs.requested_charitable_contribution < ZERO:
        raise InputValidationError("charitable contribution must be zero or greater")

    donated_shares = whole_donation_shares(
        inputs.requested_charitable_contribution, inputs.sale_price_per_share
    )
    if donated_shares > inputs.total_shares:
        raise InputValidationError(
            "the charitable contribution converts to "
            f"{donated_shares:,} donated shares, exceeding the "
            f"{inputs.total_shares:,} available shares"
        )


def calculate_scenario(
    inputs: SaleInputs, donated_shares: int, label: str
) -> ScenarioResult:
    """Calculate one alternative using the documented tax assumptions."""

    if donated_shares < 0 or donated_shares > inputs.total_shares:
        raise InputValidationError("donated shares must be between zero and total shares")

    shares_sold = inputs.total_shares - donated_shares
    donation_value = Decimal(donated_shares) * inputs.sale_price_per_share
    gross_proceeds = Decimal(shares_sold) * inputs.sale_price_per_share
    sold_share_cost_basis = Decimal(shares_sold) * inputs.cost_basis_per_share
    realized_long_term_gain = gross_proceeds - sold_share_cost_basis

    # In this model, realized long-term gain is the taxpayer's AGI and NII.
    agi = realized_long_term_gain
    contribution_percentage_limit = (
        agi * APPRECIATED_STOCK_PUBLIC_CHARITY_LIMIT_RATE
    )
    contribution_subject_to_limit = min(donation_value, contribution_percentage_limit)
    charitable_floor = agi * CHARITABLE_FLOOR_RATE
    floor_disallowed = min(contribution_subject_to_limit, charitable_floor)
    deduction_before_section_68 = contribution_subject_to_limit - floor_disallowed
    percentage_limit_excess = max(ZERO, donation_value - contribution_percentage_limit)

    # If the 30% limit is exceeded, the floor-disallowed amount joins the
    # potential five-year carryforward. Otherwise, the floor amount is lost.
    potential_carryforward = percentage_limit_excess
    if percentage_limit_excess > ZERO:
        potential_carryforward += floor_disallowed

    # Section 68 reduces deductions by 2/37 of the lesser of the deductions
    # or taxable income above the 37% bracket threshold. This model contains
    # only the charitable deduction, so no other itemized deductions appear.
    taxable_income_before_section_68 = max(
        ZERO, agi - deduction_before_section_68
    )
    section_68_income_excess = max(
        ZERO, taxable_income_before_section_68 - SECTION_68_MFJ_THRESHOLD
    )
    section_68_reduction = SECTION_68_REDUCTION_RATE * min(
        deduction_before_section_68, section_68_income_excess
    )
    allowed_charitable_deduction = deduction_before_section_68 - section_68_reduction

    # With only large long-term gain income, the regular-tax saving from the
    # itemized deduction is modeled at the high-income 20% LTCG rate. NIIT is
    # based on MAGI and therefore is not reduced by itemized deductions.
    ltcg_tax_before_deduction = realized_long_term_gain * LTCG_RATE
    charitable_deduction_tax_benefit = LTCG_RATE * min(
        allowed_charitable_deduction, realized_long_term_gain
    )
    ltcg_tax_after_deduction = (
        ltcg_tax_before_deduction - charitable_deduction_tax_benefit
    )
    niit_tax_base = min(
        realized_long_term_gain, max(ZERO, agi - NIIT_MFJ_THRESHOLD)
    )
    niit = niit_tax_base * NIIT_RATE
    total_federal_tax = ltcg_tax_after_deduction + niit
    liquid_net_after_tax = gross_proceeds - total_federal_tax

    return ScenarioResult(
        label=label,
        donated_shares=donated_shares,
        donation_value=donation_value,
        shares_sold=shares_sold,
        gross_proceeds=gross_proceeds,
        sold_share_cost_basis=sold_share_cost_basis,
        realized_long_term_gain=realized_long_term_gain,
        agi=agi,
        contribution_percentage_limit=contribution_percentage_limit,
        contribution_subject_to_limit=contribution_subject_to_limit,
        charitable_floor=charitable_floor,
        floor_disallowed=floor_disallowed,
        percentage_limit_excess=percentage_limit_excess,
        potential_carryforward=potential_carryforward,
        deduction_before_section_68=deduction_before_section_68,
        taxable_income_before_section_68=taxable_income_before_section_68,
        section_68_income_excess=section_68_income_excess,
        section_68_reduction=section_68_reduction,
        allowed_charitable_deduction=allowed_charitable_deduction,
        ltcg_tax_before_deduction=ltcg_tax_before_deduction,
        charitable_deduction_tax_benefit=charitable_deduction_tax_benefit,
        ltcg_tax_after_deduction=ltcg_tax_after_deduction,
        niit_tax_base=niit_tax_base,
        niit=niit,
        total_federal_tax=total_federal_tax,
        liquid_net_after_tax=liquid_net_after_tax,
    )


def calculate_comparison(inputs: SaleInputs) -> ComparisonResult:
    """Build the no-contribution and in-kind-donation alternatives."""

    validate_inputs(inputs)
    donation_shares = whole_donation_shares(
        inputs.requested_charitable_contribution, inputs.sale_price_per_share
    )
    return ComparisonResult(
        requested_contribution=inputs.requested_charitable_contribution,
        donation_shares=donation_shares,
        actual_donation_value=Decimal(donation_shares) * inputs.sale_price_per_share,
        no_contribution=calculate_scenario(inputs, 0, "No charitable contribution"),
        in_kind_donation=calculate_scenario(
            inputs, donation_shares, "In-kind stock donation before sale"
        ),
    )


def calculate_donation_optimization(inputs: SaleInputs) -> DonationOptimizationResult:
    """Find the largest whole-share gift with the best deduction-benefit rate.

    Below the appreciated-stock percentage limit, the deduction-benefit rate
    increases as the gift grows. Above it, the rate falls because the
    deductible amount is capped while the gift keeps growing. Therefore the
    maximum is at one of the two whole-share values straddling that limit; this
    evaluates both values instead of iterating through every available share.
    """

    validate_inputs(inputs)
    initial_gross_proceeds = (
        Decimal(inputs.total_shares) * inputs.sale_price_per_share
    )
    gross_sales_ceiling = initial_gross_proceeds * Decimal("0.30")
    maximum_donation_shares = whole_donation_shares(
        gross_sales_ceiling, inputs.sale_price_per_share
    )
    if maximum_donation_shares == 0:
        raise InputValidationError(
            "automatic mode needs at least one whole share within the 30% "
            "gross-sales ceiling"
        )

    gain_per_share = inputs.sale_price_per_share - inputs.cost_basis_per_share
    percentage_limit_boundary = (
        APPRECIATED_STOCK_PUBLIC_CHARITY_LIMIT_RATE
        * Decimal(inputs.total_shares)
        * gain_per_share
        / (
            inputs.sale_price_per_share
            + APPRECIATED_STOCK_PUBLIC_CHARITY_LIMIT_RATE * gain_per_share
        )
    )
    boundary_floor = int(
        percentage_limit_boundary.to_integral_value(rounding=ROUND_FLOOR)
    )
    candidate_shares = {
        1,
        maximum_donation_shares,
        boundary_floor - 1,
        boundary_floor,
        boundary_floor + 1,
    }
    candidate_shares = {
        shares for shares in candidate_shares if 1 <= shares <= maximum_donation_shares
    }

    best_result: ScenarioResult | None = None
    best_percentage: Decimal | None = None
    for donated_shares in sorted(candidate_shares):
        scenario = calculate_scenario(
            inputs, donated_shares, "In-kind stock donation before sale"
        )
        tax_savings_percentage = (
            scenario.charitable_deduction_tax_benefit / scenario.donation_value
        )
        if (
            best_percentage is None
            or tax_savings_percentage > best_percentage
            or (
                tax_savings_percentage == best_percentage
                and best_result is not None
                and donated_shares > best_result.donated_shares
            )
        ):
            best_result = scenario
            best_percentage = tax_savings_percentage

    assert best_result is not None
    assert best_percentage is not None
    selected_inputs = replace(
        inputs, requested_charitable_contribution=best_result.donation_value
    )
    comparison = calculate_comparison(selected_inputs)
    return DonationOptimizationResult(
        initial_gross_proceeds=initial_gross_proceeds,
        gross_sales_ceiling=gross_sales_ceiling,
        maximum_donation_shares=maximum_donation_shares,
        selected_donation_shares=best_result.donated_shares,
        selected_donation_value=best_result.donation_value,
        charitable_deduction_tax_benefit=(
            best_result.charitable_deduction_tax_benefit
        ),
        tax_savings_percentage=best_percentage,
        comparison=comparison,
    )


def format_currency(amount: Decimal) -> str:
    """Render a Decimal as a rounded, comma-separated dollar amount."""

    return f"${amount.quantize(CENT, rounding=ROUND_HALF_UP):,.2f}"


def format_shares(shares: int) -> str:
    """Render a whole share count."""

    return f"{shares:,}"


def print_scenario(result: ScenarioResult) -> None:
    """Print a human-readable scenario report."""

    print(f"\n{'=' * 78}\n{result.label}\n{'=' * 78}")
    print(f"Shares sold:                         {format_shares(result.shares_sold)}")
    print(f"Donated shares:                      {format_shares(result.donated_shares)}")
    print(f"Value of donated shares:             {format_currency(result.donation_value)}")
    print(f"Gross sale proceeds:                 {format_currency(result.gross_proceeds)}")
    print(f"Cost basis of shares sold:           {format_currency(result.sold_share_cost_basis)}")
    print(f"Realized long-term capital gain:     {format_currency(result.realized_long_term_gain)}")

    print("\nCharitable deduction mechanics")
    print(f"AGI / contribution base:             {format_currency(result.agi)}")
    print(
        "30% appreciated-stock limit:          "
        f"{format_currency(result.contribution_percentage_limit)}"
    )
    print(
        "Gift after 30% limit:                  "
        f"{format_currency(result.contribution_subject_to_limit)}"
    )
    print(f"0.5% AGI floor:                       {format_currency(result.charitable_floor)}")
    print(f"Floor disallowed:                     {format_currency(result.floor_disallowed)}")
    print(
        "30% limit excess:                      "
        f"{format_currency(result.percentage_limit_excess)}"
    )
    print(
        "Potential five-year carryforward:      "
        f"{format_currency(result.potential_carryforward)}"
    )
    print(
        "Deduction before Section 68:           "
        f"{format_currency(result.deduction_before_section_68)}"
    )
    print(
        "Taxable income before Section 68:      "
        f"{format_currency(result.taxable_income_before_section_68)}"
    )
    print(
        f"Income above ${SECTION_68_MFJ_THRESHOLD:,.0f}:          "
        f"{format_currency(result.section_68_income_excess)}"
    )
    print(
        "Section 68 haircut (2/37):             "
        f"{format_currency(result.section_68_reduction)}"
    )
    print(
        "Allowed charitable deduction:           "
        f"{format_currency(result.allowed_charitable_deduction)}"
    )

    print("\nFederal taxes")
    print(
        f"LTCG tax before deduction ({LTCG_RATE:.1%}):     "
        f"{format_currency(result.ltcg_tax_before_deduction)}"
    )
    print(
        "Less charitable deduction tax benefit:  "
        f"-{format_currency(result.charitable_deduction_tax_benefit)}"
    )
    print(
        "LTCG tax after deduction:               "
        f"{format_currency(result.ltcg_tax_after_deduction)}"
    )
    print(
        f"NIIT taxable base above ${NIIT_MFJ_THRESHOLD:,.0f}:      "
        f"{format_currency(result.niit_tax_base)}"
    )
    print(f"NIIT ({NIIT_RATE:.1%}):                         {format_currency(result.niit)}")
    print(f"Total federal tax:                     {format_currency(result.total_federal_tax)}")
    print(f"Liquid net after federal tax:          {format_currency(result.liquid_net_after_tax)}")


def print_comparison(
    comparison: ComparisonResult,
    contribution_label: str = "Requested charitable contribution",
) -> None:
    """Print both scenarios and the conversion from dollars to whole shares."""

    print(f"Tax year {TAX_YEAR} federal illustration — married filing jointly")
    print(
        f"{contribution_label}:      "
        f"{format_currency(comparison.requested_contribution)}"
    )
    print(
        "Whole donated shares (rounded down):    "
        f"{format_shares(comparison.donation_shares)}"
    )
    print(
        "Actual in-kind donation value:           "
        f"{format_currency(comparison.actual_donation_value)}"
    )
    print_scenario(comparison.no_contribution)
    print_scenario(comparison.in_kind_donation)
    print("\nNotes")
    print(
        "- The charitable deduction reduces regular LTCG tax at the modeled "
        "20% rate; it does not reduce NIIT."
    )
    print(
        "- A floor-disallowed amount is shown as a potential carryforward only "
        "when the 30% limit is exceeded; later-year ordering is not modeled."
    )
    print(
        "- This excludes other income, deductions, credits, state taxes, and "
        "the complete capital-gain rate schedule. Consult a tax professional."
    )


def print_donation_optimization(result: DonationOptimizationResult) -> None:
    """Print the selected automatic gift before the standard comparison."""

    print("Automatic donation optimization")
    print(
        "Initial gross sale proceeds:             "
        f"{format_currency(result.initial_gross_proceeds)}"
    )
    print(
        "30% gross-sales donation ceiling:        "
        f"{format_currency(result.gross_sales_ceiling)}"
    )
    print(
        "Maximum whole shares within ceiling:     "
        f"{format_shares(result.maximum_donation_shares)}"
    )
    print(
        "Selected donated shares:                 "
        f"{format_shares(result.selected_donation_shares)}"
    )
    print(
        "Selected in-kind donation value:         "
        f"{format_currency(result.selected_donation_value)}"
    )
    print(
        "Charitable deduction tax benefit:        "
        f"{format_currency(result.charitable_deduction_tax_benefit)}"
    )
    print(
        "Tax-savings percentage of donation:      "
        f"{result.tax_savings_percentage:.1%}"
    )
    print(
        "(This percentage excludes LTCG and NIIT avoided because donated "
        "shares are not sold.)\n"
    )
    print_comparison(result.comparison, "Selected charitable contribution")


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line interface and its usage documentation."""

    parser = argparse.ArgumentParser(
        description=(
            "Compare a full long-term stock sale with an in-kind public-charity "
            "stock donation made before the remaining shares are sold."
        ),
        epilog=(
            "Example:\n"
            "  python3 charitable_stock_sale.py --total-shares 100000 "
            "--cost-basis-per-share 100 --sale-price-per-share 500 "
            "--charitable-contribution 10000000\n"
            "  python3 charitable_stock_sale.py --total-shares 100000 "
            "--cost-basis-per-share 100 --sale-price-per-share 500 "
            "--maximize-tax-savings-percentage\n\n"
            "This simplified 2026 federal illustration assumes married filing "
            "jointly, long-term gain as the only income, and a qualifying public "
            "charity. It is not tax advice."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--total-shares",
        required=True,
        type=parse_positive_whole_shares,
        help="Total whole shares owned and otherwise available for sale.",
    )
    parser.add_argument(
        "--cost-basis-per-share",
        required=True,
        type=parse_nonnegative_decimal,
        help="Average cost basis per share; it must be below the sale price.",
    )
    parser.add_argument(
        "--sale-price-per-share",
        required=True,
        type=parse_positive_decimal,
        help="Assumed sale price and fair-market value per share.",
    )
    parser.add_argument(
        "--charitable-contribution",
        type=parse_nonnegative_decimal,
        help=(
            "Requested dollar gift; converted to whole donated shares by rounding "
            "down. Required unless --maximize-tax-savings-percentage is used."
        ),
    )
    parser.add_argument(
        "--maximize-tax-savings-percentage",
        action="store_true",
        help=(
            "Automatically select the whole-share gift, up to 30%% of initial "
            "gross sale proceeds, with the highest deduction-only tax-benefit "
            "percentage. Do not combine with --charitable-contribution."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and turn validation failures into useful argument errors."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.maximize_tax_savings_percentage and args.charitable_contribution is not None:
        parser.error(
            "--charitable-contribution cannot be used with "
            "--maximize-tax-savings-percentage"
        )
    if not args.maximize_tax_savings_percentage and args.charitable_contribution is None:
        parser.error(
            "--charitable-contribution is required unless "
            "--maximize-tax-savings-percentage is used"
        )

    inputs = SaleInputs(
        total_shares=args.total_shares,
        cost_basis_per_share=args.cost_basis_per_share,
        sale_price_per_share=args.sale_price_per_share,
        requested_charitable_contribution=(
            ZERO
            if args.charitable_contribution is None
            else args.charitable_contribution
        ),
    )
    try:
        if args.maximize_tax_savings_percentage:
            print_donation_optimization(calculate_donation_optimization(inputs))
        else:
            print_comparison(calculate_comparison(inputs))
    except InputValidationError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

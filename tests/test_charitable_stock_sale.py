"""Focused tests for the charitable stock sale calculator."""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from charitable_stock_sale import (  # noqa: E402
    InputValidationError,
    SaleInputs,
    calculate_comparison,
    calculate_donation_optimization,
    calculate_scenario,
)


class CharitableStockSaleTests(unittest.TestCase):
    def test_comparison_excludes_donated_shares_from_sale_and_gain(self) -> None:
        inputs = SaleInputs(
            total_shares=1_000_000,
            cost_basis_per_share=Decimal("10"),
            sale_price_per_share=Decimal("100"),
            requested_charitable_contribution=Decimal("1000000"),
        )

        comparison = calculate_comparison(inputs)

        self.assertEqual(comparison.donation_shares, 10_000)
        self.assertEqual(comparison.actual_donation_value, Decimal("1000000"))
        self.assertEqual(comparison.no_contribution.shares_sold, 1_000_000)
        self.assertEqual(comparison.in_kind_donation.shares_sold, 990_000)
        self.assertEqual(
            comparison.in_kind_donation.gross_proceeds, Decimal("99000000")
        )
        self.assertEqual(
            comparison.in_kind_donation.realized_long_term_gain, Decimal("89100000")
        )
        self.assertLess(
            comparison.in_kind_donation.total_federal_tax,
            comparison.no_contribution.total_federal_tax,
        )

    def test_donation_dollars_round_down_to_whole_shares(self) -> None:
        inputs = SaleInputs(
            total_shares=100,
            cost_basis_per_share=Decimal("100"),
            sale_price_per_share=Decimal("333.33"),
            requested_charitable_contribution=Decimal("1000"),
        )

        comparison = calculate_comparison(inputs)

        self.assertEqual(comparison.donation_shares, 3)
        self.assertEqual(comparison.actual_donation_value, Decimal("999.99"))
        self.assertEqual(comparison.in_kind_donation.shares_sold, 97)

    def test_donation_converting_to_more_than_available_shares_is_rejected(self) -> None:
        inputs = SaleInputs(
            total_shares=5,
            cost_basis_per_share=Decimal("10"),
            sale_price_per_share=Decimal("100"),
            requested_charitable_contribution=Decimal("600"),
        )

        with self.assertRaisesRegex(InputValidationError, "exceeding"):
            calculate_comparison(inputs)

    def test_appreciated_stock_percentage_limit_and_floor_carryforward(self) -> None:
        inputs = SaleInputs(
            total_shares=1_000_000,
            cost_basis_per_share=Decimal("1"),
            sale_price_per_share=Decimal("100"),
            requested_charitable_contribution=Decimal("40000000"),
        )

        result = calculate_comparison(inputs).in_kind_donation

        self.assertEqual(result.donation_value, Decimal("40000000"))
        self.assertEqual(result.realized_long_term_gain, Decimal("59400000"))
        self.assertEqual(result.contribution_percentage_limit, Decimal("17820000.00"))
        self.assertEqual(result.charitable_floor, Decimal("297000.000"))
        self.assertEqual(result.deduction_before_section_68, Decimal("17523000.000"))
        self.assertEqual(result.percentage_limit_excess, Decimal("22180000.00"))
        self.assertEqual(result.potential_carryforward, Decimal("22477000.000"))

    def test_automatic_mode_selects_best_whole_share_donation(self) -> None:
        inputs = SaleInputs(
            total_shares=50_000,
            cost_basis_per_share=Decimal("70"),
            sale_price_per_share=Decimal("700"),
            requested_charitable_contribution=Decimal("0"),
        )

        result = calculate_donation_optimization(inputs)

        self.assertEqual(result.initial_gross_proceeds, Decimal("35000000"))
        self.assertEqual(result.gross_sales_ceiling, Decimal("10500000.00"))
        self.assertEqual(result.maximum_donation_shares, 15_000)
        self.assertEqual(result.selected_donation_shares, 10_629)
        self.assertEqual(result.selected_donation_value, Decimal("7440300"))
        self.assertLessEqual(
            result.selected_donation_value, result.gross_sales_ceiling
        )
        self.assertEqual(
            result.charitable_deduction_tax_benefit,
            Decimal("7316281.35") * Decimal(7) / Decimal(37),
        )
        self.assertEqual(
            result.tax_savings_percentage,
            result.charitable_deduction_tax_benefit / result.selected_donation_value,
        )

    def test_manual_donation_mode_remains_available(self) -> None:
        inputs = SaleInputs(
            total_shares=50_000,
            cost_basis_per_share=Decimal("70"),
            sale_price_per_share=Decimal("700"),
            requested_charitable_contribution=Decimal("5000000"),
        )

        comparison = calculate_comparison(inputs)

        self.assertEqual(comparison.donation_shares, 7_142)
        self.assertEqual(comparison.actual_donation_value, Decimal("4999400"))

    def test_automatic_mode_selects_largest_best_percentage_in_small_search(self) -> None:
        inputs = SaleInputs(
            total_shares=100,
            cost_basis_per_share=Decimal("70"),
            sale_price_per_share=Decimal("700"),
            requested_charitable_contribution=Decimal("0"),
        )

        result = calculate_donation_optimization(inputs)

        self.assertEqual(result.maximum_donation_shares, 30)
        for donated_shares in range(1, result.maximum_donation_shares + 1):
            scenario = calculate_scenario(inputs, donated_shares, "test")
            percentage = (
                scenario.charitable_deduction_tax_benefit / scenario.donation_value
            )
            self.assertLessEqual(percentage, result.tax_savings_percentage)
            if percentage == result.tax_savings_percentage:
                self.assertLessEqual(donated_shares, result.selected_donation_shares)


if __name__ == "__main__":
    unittest.main()

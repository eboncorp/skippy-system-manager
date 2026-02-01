"""
Tax reporting module.

Generates tax reports for:
- Capital gains/losses (Form 8949)
- Staking income (reported as ordinary income)
- Cost basis tracking with multiple methods (FIFO, LIFO, HIFO, Specific ID)
"""

import csv
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from data.storage import db


class CostBasisMethod(Enum):
    """Methods for calculating cost basis on sales."""
    FIFO = "fifo"      # First In, First Out
    LIFO = "lifo"      # Last In, First Out
    HIFO = "hifo"      # Highest In, First Out (minimizes gains)
    SPECIFIC_ID = "specific_id"  # Specific identification


@dataclass
class TaxLot:
    """A tax lot representing an acquisition of crypto."""
    id: int
    asset: str
    amount: Decimal
    cost_basis: Decimal  # Total cost in USD
    acquisition_date: datetime
    source: str  # "purchase", "dca", "staking_reward", "airdrop", etc.
    remaining_amount: Decimal

    @property
    def cost_per_unit(self) -> Decimal:
        """Cost per unit of the asset."""
        if self.amount == 0:
            return Decimal("0")
        return self.cost_basis / self.amount

    @property
    def is_long_term(self) -> bool:
        """Whether this lot qualifies for long-term capital gains (held > 1 year)."""
        return (datetime.now() - self.acquisition_date).days > 365


@dataclass
class CapitalGain:
    """A capital gain or loss from a sale."""
    asset: str
    date_acquired: datetime
    date_sold: datetime
    proceeds: Decimal
    cost_basis: Decimal
    gain_loss: Decimal
    is_long_term: bool
    amount_sold: Decimal

    @property
    def holding_period(self) -> str:
        """Holding period for tax purposes."""
        return "Long-term" if self.is_long_term else "Short-term"


@dataclass
class StakingIncome:
    """Staking reward taxed as ordinary income."""
    asset: str
    amount: Decimal
    usd_value: Decimal
    date_received: datetime
    source: str


@dataclass
class TaxSummary:
    """Complete tax summary for a year."""
    year: int

    # Capital gains
    short_term_gains: Decimal = Decimal("0")
    short_term_losses: Decimal = Decimal("0")
    long_term_gains: Decimal = Decimal("0")
    long_term_losses: Decimal = Decimal("0")
    capital_gains_transactions: List[CapitalGain] = field(default_factory=list)

    # Income
    staking_income: Decimal = Decimal("0")
    staking_transactions: List[StakingIncome] = field(default_factory=list)

    @property
    def net_short_term(self) -> Decimal:
        return self.short_term_gains - self.short_term_losses

    @property
    def net_long_term(self) -> Decimal:
        return self.long_term_gains - self.long_term_losses

    @property
    def total_capital_gain_loss(self) -> Decimal:
        return self.net_short_term + self.net_long_term

    @property
    def total_ordinary_income(self) -> Decimal:
        return self.staking_income


class TaxCalculator:
    """Calculates taxes for crypto transactions."""

    def __init__(self, method: CostBasisMethod = CostBasisMethod.FIFO):
        self.method = method

    def get_tax_lots(self, asset: str) -> List[TaxLot]:
        """Get all open tax lots for an asset."""
        lots_data = db.get_open_tax_lots(asset)
        return [
            TaxLot(
                id=lot["id"],
                asset=lot["asset"],
                amount=lot["amount"],
                cost_basis=lot["cost_basis"],
                acquisition_date=lot["acquisition_date"],
                source=lot["source"],
                remaining_amount=lot["remaining_amount"],
            )
            for lot in lots_data
        ]

    def select_lots_for_sale(
        self,
        asset: str,
        amount_to_sell: Decimal,
        method: Optional[CostBasisMethod] = None,
    ) -> List[Tuple[TaxLot, Decimal]]:
        """
        Select which tax lots to use for a sale.

        Returns:
            List of (lot, amount_from_lot) tuples
        """
        method = method or self.method
        lots = self.get_tax_lots(asset)

        if not lots:
            raise ValueError(f"No tax lots available for {asset}")

        # Sort lots based on method
        if method == CostBasisMethod.FIFO:
            lots.sort(key=lambda x: x.acquisition_date)
        elif method == CostBasisMethod.LIFO:
            lots.sort(key=lambda x: x.acquisition_date, reverse=True)
        elif method == CostBasisMethod.HIFO:
            lots.sort(key=lambda x: x.cost_per_unit, reverse=True)
        # SPECIFIC_ID would require manual selection

        selected = []
        remaining_to_sell = amount_to_sell

        for lot in lots:
            if remaining_to_sell <= 0:
                break

            amount_from_lot = min(lot.remaining_amount, remaining_to_sell)
            if amount_from_lot > 0:
                selected.append((lot, amount_from_lot))
                remaining_to_sell -= amount_from_lot

        if remaining_to_sell > 0:
            raise ValueError(
                f"Insufficient {asset} in tax lots. "
                f"Tried to sell {amount_to_sell}, only {amount_to_sell - remaining_to_sell} available."
            )

        return selected

    def calculate_gain(
        self,
        asset: str,
        amount_sold: Decimal,
        proceeds: Decimal,
        sale_date: datetime,
        method: Optional[CostBasisMethod] = None,
    ) -> List[CapitalGain]:
        """
        Calculate capital gain/loss for a sale.

        This also updates the tax lots in the database.
        """
        selected_lots = self.select_lots_for_sale(asset, amount_sold, method)
        gains = []

        for lot, amount_from_lot in selected_lots:
            # Calculate proportional proceeds and cost basis
            proportion = amount_from_lot / amount_sold
            lot_proceeds = proceeds * proportion
            lot_cost_basis = lot.cost_per_unit * amount_from_lot

            gain_loss = lot_proceeds - lot_cost_basis
            is_long_term = (sale_date - lot.acquisition_date).days > 365

            gains.append(CapitalGain(
                asset=asset,
                date_acquired=lot.acquisition_date,
                date_sold=sale_date,
                proceeds=lot_proceeds,
                cost_basis=lot_cost_basis,
                gain_loss=gain_loss,
                is_long_term=is_long_term,
                amount_sold=amount_from_lot,
            ))

            # Update the tax lot in database
            db.close_tax_lot(
                lot_id=lot.id,
                amount_sold=amount_from_lot,
                proceeds=lot_proceeds,
                close_date=sale_date,
            )

        return gains

    def get_staking_income(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[StakingIncome]:
        """Get staking income for a period."""
        rewards = db.get_staking_rewards(start_date=start_date, end_date=end_date)

        return [
            StakingIncome(
                asset=r["asset"],
                amount=r["amount"],
                usd_value=r["usd_value"],
                date_received=r["timestamp"],
                source=r["source"],
            )
            for r in rewards
        ]

    def generate_tax_summary(self, year: int) -> TaxSummary:
        """Generate complete tax summary for a year."""
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        summary = TaxSummary(year=year)

        # Get capital gains from database
        # Note: In a full implementation, you'd track all sales
        # For now, we'll just get staking income

        # Get staking income
        staking = self.get_staking_income(start_date, end_date)
        summary.staking_transactions = staking
        summary.staking_income = sum(s.usd_value for s in staking)

        return summary


class TaxReportGenerator:
    """Generates tax reports and exports."""

    def __init__(self, calculator: TaxCalculator):
        self.calculator = calculator

    def export_form_8949(
        self,
        gains: List[CapitalGain],
        filepath: str,
        part: str = "both",  # "short", "long", or "both"
    ):
        """
        Export capital gains in IRS Form 8949 format.

        Form 8949 columns:
        (a) Description of property
        (b) Date acquired
        (c) Date sold
        (d) Proceeds
        (e) Cost or other basis
        (f) Adjustment code (if any)
        (g) Amount of adjustment
        (h) Gain or (loss)
        """
        # Filter by holding period
        if part == "short":
            gains = [g for g in gains if not g.is_long_term]
        elif part == "long":
            gains = [g for g in gains if g.is_long_term]

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "Description of Property (a)",
                "Date Acquired (b)",
                "Date Sold (c)",
                "Proceeds (d)",
                "Cost Basis (e)",
                "Adjustment Code (f)",
                "Adjustment Amount (g)",
                "Gain or Loss (h)",
            ])

            for gain in sorted(gains, key=lambda x: x.date_sold):
                writer.writerow([
                    f"{float(gain.amount_sold):.8f} {gain.asset}",
                    gain.date_acquired.strftime("%m/%d/%Y"),
                    gain.date_sold.strftime("%m/%d/%Y"),
                    f"{float(gain.proceeds):.2f}",
                    f"{float(gain.cost_basis):.2f}",
                    "",  # Adjustment code
                    "",  # Adjustment amount
                    f"{float(gain.gain_loss):.2f}",
                ])

            # Summary row
            total_proceeds = sum(g.proceeds for g in gains)
            total_cost = sum(g.cost_basis for g in gains)
            total_gain = sum(g.gain_loss for g in gains)

            writer.writerow([])
            writer.writerow([
                "TOTALS",
                "",
                "",
                f"{float(total_proceeds):.2f}",
                f"{float(total_cost):.2f}",
                "",
                "",
                f"{float(total_gain):.2f}",
            ])

    def export_staking_income(
        self,
        income: List[StakingIncome],
        filepath: str,
    ):
        """Export staking income report."""
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)

            writer.writerow([
                "Date Received",
                "Asset",
                "Amount",
                "Fair Market Value (USD)",
                "Source",
            ])

            for inc in sorted(income, key=lambda x: x.date_received):
                writer.writerow([
                    inc.date_received.strftime("%m/%d/%Y"),
                    inc.asset,
                    f"{float(inc.amount):.8f}",
                    f"{float(inc.usd_value):.2f}",
                    inc.source,
                ])

            # Summary
            total = sum(i.usd_value for i in income)
            writer.writerow([])
            writer.writerow(["TOTAL STAKING INCOME", "", "", f"{float(total):.2f}", ""])

    def generate_full_report(
        self,
        year: int,
        output_dir: str = "./data/tax_reports",
    ) -> Dict[str, str]:
        """
        Generate all tax reports for a year.

        Returns:
            Dict mapping report name to filepath
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        summary = self.calculator.generate_tax_summary(year)
        reports = {}

        # Form 8949 - Short-term
        if summary.capital_gains_transactions:
            short_term = [g for g in summary.capital_gains_transactions if not g.is_long_term]
            if short_term:
                filepath = str(output_path / f"form_8949_short_term_{year}.csv")
                self.export_form_8949(short_term, filepath, part="short")
                reports["form_8949_short_term"] = filepath

            # Form 8949 - Long-term
            long_term = [g for g in summary.capital_gains_transactions if g.is_long_term]
            if long_term:
                filepath = str(output_path / f"form_8949_long_term_{year}.csv")
                self.export_form_8949(long_term, filepath, part="long")
                reports["form_8949_long_term"] = filepath

        # Staking income
        if summary.staking_transactions:
            filepath = str(output_path / f"staking_income_{year}.csv")
            self.export_staking_income(summary.staking_transactions, filepath)
            reports["staking_income"] = filepath

        # Summary report
        summary_filepath = str(output_path / f"tax_summary_{year}.txt")
        self._write_summary(summary, summary_filepath)
        reports["summary"] = summary_filepath

        return reports

    def _write_summary(self, summary: TaxSummary, filepath: str):
        """Write a human-readable tax summary."""
        with open(filepath, "w") as f:
            f.write(f"TAX SUMMARY - {summary.year}\n")
            f.write("=" * 50 + "\n\n")

            f.write("CAPITAL GAINS/LOSSES\n")
            f.write("-" * 30 + "\n")
            f.write(f"Short-term gains:   ${float(summary.short_term_gains):>12,.2f}\n")
            f.write(f"Short-term losses:  ${float(summary.short_term_losses):>12,.2f}\n")
            f.write(f"Net short-term:     ${float(summary.net_short_term):>12,.2f}\n")
            f.write("\n")
            f.write(f"Long-term gains:    ${float(summary.long_term_gains):>12,.2f}\n")
            f.write(f"Long-term losses:   ${float(summary.long_term_losses):>12,.2f}\n")
            f.write(f"Net long-term:      ${float(summary.net_long_term):>12,.2f}\n")
            f.write("\n")
            f.write(f"TOTAL CAPITAL GAIN/LOSS: ${float(summary.total_capital_gain_loss):>12,.2f}\n")
            f.write("\n\n")

            f.write("ORDINARY INCOME (STAKING)\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total staking income: ${float(summary.staking_income):>12,.2f}\n")
            f.write(f"Number of rewards:    {len(summary.staking_transactions):>12}\n")
            f.write("\n")

            # Breakdown by asset
            if summary.staking_transactions:
                f.write("By Asset:\n")
                by_asset: Dict[str, Decimal] = {}
                for s in summary.staking_transactions:
                    if s.asset not in by_asset:
                        by_asset[s.asset] = Decimal("0")
                    by_asset[s.asset] += s.usd_value

                for asset, total in sorted(by_asset.items(), key=lambda x: -x[1]):
                    f.write(f"  {asset}: ${float(total):,.2f}\n")

            f.write("\n\n")
            f.write("IMPORTANT NOTES\n")
            f.write("-" * 30 + "\n")
            f.write("1. This is for informational purposes only.\n")
            f.write("2. Consult a tax professional for advice.\n")
            f.write("3. Staking rewards are taxed as ordinary income at FMV when received.\n")
            f.write("4. The cost basis of staking rewards becomes the FMV at receipt.\n")


def format_tax_summary(summary: TaxSummary) -> str:
    """Format tax summary for display."""
    lines = []
    lines.append(f"Tax Summary - {summary.year}")
    lines.append("=" * 50)

    lines.append("\nCapital Gains/Losses:")
    lines.append(f"  Short-term: ${float(summary.net_short_term):+,.2f}")
    lines.append(f"  Long-term:  ${float(summary.net_long_term):+,.2f}")
    lines.append(f"  Total:      ${float(summary.total_capital_gain_loss):+,.2f}")

    lines.append(f"\nStaking Income: ${float(summary.staking_income):,.2f}")
    lines.append(f"  ({len(summary.staking_transactions)} reward transactions)")

    return "\n".join(lines)

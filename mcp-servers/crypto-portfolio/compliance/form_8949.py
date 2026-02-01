"""
IRS Form 8949 & Schedule D Generation
======================================

Generates IRS-compliant Form 8949 (Sales and Dispositions of Capital Assets)
and Schedule D summaries for cryptocurrency transactions.

Form 8949 separates transactions into:
- Part I: Short-term (held 1 year or less)
- Part II: Long-term (held more than 1 year)

Each part uses checkbox boxes A-F to indicate basis reporting:
- Box A/D: Reported to IRS, basis reported
- Box B/E: Reported to IRS, basis NOT reported
- Box C/F: NOT reported to IRS
"""

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional


class Form8949Box(str, Enum):
    """IRS Form 8949 checkbox categories."""
    A = "A"  # Short-term, basis reported to IRS
    B = "B"  # Short-term, basis NOT reported to IRS
    C = "C"  # Short-term, NOT reported to IRS
    D = "D"  # Long-term, basis reported to IRS
    E = "E"  # Long-term, basis NOT reported to IRS
    F = "F"  # Long-term, NOT reported to IRS


@dataclass
class Form8949Line:
    """A single line on Form 8949."""
    description: str          # (a) e.g. "0.50000000 BTC"
    date_acquired: datetime   # (b)
    date_sold: datetime       # (c)
    proceeds: Decimal         # (d)
    cost_basis: Decimal       # (e)
    adjustment_code: str = "" # (f) e.g. "W" for wash sale
    adjustment_amount: Decimal = Decimal("0")  # (g)
    box: Form8949Box = Form8949Box.C  # Default: not reported to IRS (crypto)

    # Extra metadata (not on the form, but useful for tracking)
    asset: str = ""
    exchange: str = ""
    transaction_id: str = ""

    @property
    def gain_or_loss(self) -> Decimal:
        """Column (h): Gain or (loss). Proceeds - basis + adjustment."""
        return self.proceeds - self.cost_basis + self.adjustment_amount

    @property
    def holding_period_days(self) -> int:
        """Days between acquisition and sale."""
        return (self.date_sold - self.date_acquired).days

    @property
    def is_long_term(self) -> bool:
        """Whether held more than 1 year (365 days)."""
        return self.holding_period_days > 365


# Number of data lines per Form 8949 page (IRS standard)
LINES_PER_PAGE = 14


class Form8949Generator:
    """Generates IRS Form 8949 output in CSV or PDF format."""

    def __init__(self, lines: List[Form8949Line], tax_year: int,
                 taxpayer_name: str = "", taxpayer_ssn: str = ""):
        self.lines = lines
        self.tax_year = tax_year
        self.taxpayer_name = taxpayer_name
        self.taxpayer_ssn = taxpayer_ssn

    def _split_by_term(self) -> tuple:
        """Split lines into short-term (Part I) and long-term (Part II)."""
        short_term = [l for l in self.lines if not l.is_long_term]
        long_term = [l for l in self.lines if l.is_long_term]
        return short_term, long_term

    def generate_csv(self) -> str:
        """Generate Form 8949 as CSV string (both parts)."""
        output = io.StringIO()
        writer = csv.writer(output)

        short_term, long_term = self._split_by_term()

        if short_term:
            self._write_part_csv(writer, short_term, "Part I - Short-Term")

        if long_term:
            if short_term:
                writer.writerow([])  # blank separator
            self._write_part_csv(writer, long_term, "Part II - Long-Term")

        return output.getvalue()

    def _write_part_csv(self, writer: csv.writer, lines: List[Form8949Line],
                        part_title: str):
        """Write one part (short or long term) to CSV."""
        writer.writerow([f"Form 8949 - {part_title} - Tax Year {self.tax_year}"])
        if self.taxpayer_name:
            writer.writerow([f"Taxpayer: {self.taxpayer_name}"])
        writer.writerow([])

        # Column headers matching IRS form
        writer.writerow([
            "(a) Description of property",
            "(b) Date acquired",
            "(c) Date sold or disposed of",
            "(d) Proceeds",
            "(e) Cost or other basis",
            "(f) Code(s)",
            "(g) Adjustment",
            "(h) Gain or (loss)",
        ])

        page_count = 0
        for i, line in enumerate(sorted(lines, key=lambda x: x.date_sold)):
            if i > 0 and i % LINES_PER_PAGE == 0:
                # Page subtotal
                page_lines = lines[page_count * LINES_PER_PAGE:i]
                self._write_totals_row(writer, page_lines, "Page Subtotal")
                writer.writerow([])
                page_count += 1

            writer.writerow([
                line.description,
                line.date_acquired.strftime("%m/%d/%Y"),
                line.date_sold.strftime("%m/%d/%Y"),
                f"{line.proceeds:.2f}",
                f"{line.cost_basis:.2f}",
                line.adjustment_code,
                f"{line.adjustment_amount:.2f}" if line.adjustment_amount else "",
                f"{line.gain_or_loss:.2f}",
            ])

        # Final totals
        writer.writerow([])
        self._write_totals_row(writer, lines, "TOTALS")

    def _write_totals_row(self, writer: csv.writer, lines: List[Form8949Line],
                          label: str):
        """Write a totals row."""
        total_proceeds = sum(l.proceeds for l in lines)
        total_basis = sum(l.cost_basis for l in lines)
        total_adjustment = sum(l.adjustment_amount for l in lines)
        total_gain = sum(l.gain_or_loss for l in lines)

        writer.writerow([
            label,
            "",
            "",
            f"{total_proceeds:.2f}",
            f"{total_basis:.2f}",
            "",
            f"{total_adjustment:.2f}" if total_adjustment else "",
            f"{total_gain:.2f}",
        ])

    def generate_pdf(self, output_path: str) -> str:
        """Generate Form 8949 as PDF. Falls back to CSV if reportlab unavailable.

        Args:
            output_path: File path for the PDF output.

        Returns:
            Path to the generated file (PDF or CSV fallback).
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
            )
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            # Fall back to CSV
            csv_path = output_path.replace(".pdf", ".csv")
            with open(csv_path, "w") as f:
                f.write(self.generate_csv())
            return csv_path

        doc = SimpleDocTemplate(output_path, pagesize=letter,
                                topMargin=0.5 * inch, bottomMargin=0.5 * inch)
        styles = getSampleStyleSheet()
        elements = []

        short_term, long_term = self._split_by_term()

        if short_term:
            elements.extend(
                self._build_pdf_part(short_term, "Part I - Short-Term",
                                     styles)
            )

        if long_term:
            elements.append(Spacer(1, 0.3 * inch))
            elements.extend(
                self._build_pdf_part(long_term, "Part II - Long-Term",
                                     styles)
            )

        doc.build(elements)
        return output_path

    def _build_pdf_part(self, lines: List[Form8949Line], title: str,
                        styles) -> list:
        """Build PDF elements for one part."""
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer

        elements = []

        # Title
        elements.append(
            Paragraph(f"<b>Form 8949 - {title} - Tax Year {self.tax_year}</b>",
                       styles["Heading2"])
        )
        if self.taxpayer_name:
            elements.append(
                Paragraph(f"Taxpayer: {self.taxpayer_name}", styles["Normal"])
            )
        elements.append(Spacer(1, 0.15 * inch))

        # Headers
        headers = ["(a) Description", "(b) Acquired", "(c) Sold",
                    "(d) Proceeds", "(e) Basis", "(f) Code",
                    "(g) Adjust.", "(h) Gain/(Loss)"]

        sorted_lines = sorted(lines, key=lambda x: x.date_sold)

        # Paginate
        for page_start in range(0, len(sorted_lines), LINES_PER_PAGE):
            page_lines = sorted_lines[page_start:page_start + LINES_PER_PAGE]

            data = [headers]
            for line in page_lines:
                data.append([
                    line.description[:30],
                    line.date_acquired.strftime("%m/%d/%y"),
                    line.date_sold.strftime("%m/%d/%y"),
                    f"${line.proceeds:,.2f}",
                    f"${line.cost_basis:,.2f}",
                    line.adjustment_code,
                    f"${line.adjustment_amount:,.2f}" if line.adjustment_amount else "",
                    f"${line.gain_or_loss:,.2f}",
                ])

            # Subtotal row
            tp = sum(l.proceeds for l in page_lines)
            tb = sum(l.cost_basis for l in page_lines)
            ta = sum(l.adjustment_amount for l in page_lines)
            tg = sum(l.gain_or_loss for l in page_lines)
            data.append([
                "Subtotal", "", "",
                f"${tp:,.2f}", f"${tb:,.2f}", "",
                f"${ta:,.2f}" if ta else "", f"${tg:,.2f}",
            ])

            col_widths = [1.8*inch, 0.7*inch, 0.7*inch, 0.9*inch,
                          0.9*inch, 0.5*inch, 0.7*inch, 0.9*inch]

            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#D9E2F3")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2),
                 [colors.white, colors.HexColor("#F2F2F2")]),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 0.15 * inch))

        return elements

    def generate_summary_markdown(self) -> str:
        """Generate a markdown summary of the Form 8949 data."""
        short_term, long_term = self._split_by_term()

        lines_out = []
        lines_out.append(f"# Form 8949 Summary - Tax Year {self.tax_year}")
        if self.taxpayer_name:
            lines_out.append(f"**Taxpayer:** {self.taxpayer_name}")
        lines_out.append("")

        for label, group in [("Short-Term (Part I)", short_term),
                             ("Long-Term (Part II)", long_term)]:
            if not group:
                continue

            total_proceeds = sum(l.proceeds for l in group)
            total_basis = sum(l.cost_basis for l in group)
            total_gain = sum(l.gain_or_loss for l in group)

            lines_out.append(f"## {label}")
            lines_out.append(f"- **Transactions:** {len(group)}")
            lines_out.append(f"- **Total Proceeds:** ${total_proceeds:,.2f}")
            lines_out.append(f"- **Total Cost Basis:** ${total_basis:,.2f}")
            lines_out.append(f"- **Net Gain/(Loss):** ${total_gain:,.2f}")
            lines_out.append("")

        # Grand totals
        all_proceeds = sum(l.proceeds for l in self.lines)
        all_basis = sum(l.cost_basis for l in self.lines)
        all_gain = sum(l.gain_or_loss for l in self.lines)

        lines_out.append("## Grand Totals")
        lines_out.append(f"- **Total Transactions:** {len(self.lines)}")
        lines_out.append(f"- **Total Proceeds:** ${all_proceeds:,.2f}")
        lines_out.append(f"- **Total Cost Basis:** ${all_basis:,.2f}")
        lines_out.append(f"- **Net Capital Gain/(Loss):** ${all_gain:,.2f}")

        return "\n".join(lines_out)


class ScheduleDGenerator:
    """Generates IRS Schedule D summary from Form 8949 data."""

    def __init__(self, lines: List[Form8949Line], tax_year: int):
        self.lines = lines
        self.tax_year = tax_year

    def generate(self) -> Dict:
        """Generate Schedule D summary data.

        Returns:
            Dict with part_i (short-term), part_ii (long-term), and net totals.
        """
        short_term = [l for l in self.lines if not l.is_long_term]
        long_term = [l for l in self.lines if l.is_long_term]

        st_proceeds = sum(l.proceeds for l in short_term)
        st_basis = sum(l.cost_basis for l in short_term)
        st_adjustments = sum(l.adjustment_amount for l in short_term)
        st_gain = sum(l.gain_or_loss for l in short_term)

        lt_proceeds = sum(l.proceeds for l in long_term)
        lt_basis = sum(l.cost_basis for l in long_term)
        lt_adjustments = sum(l.adjustment_amount for l in long_term)
        lt_gain = sum(l.gain_or_loss for l in long_term)

        return {
            "tax_year": self.tax_year,
            "part_i_short_term": {
                "description": "Short-term capital gains and losses (assets held one year or less)",
                "total_proceeds": float(st_proceeds),
                "total_cost_basis": float(st_basis),
                "total_adjustments": float(st_adjustments),
                "total_gain_or_loss": float(st_gain),
                "transaction_count": len(short_term),
            },
            "part_ii_long_term": {
                "description": "Long-term capital gains and losses (assets held more than one year)",
                "total_proceeds": float(lt_proceeds),
                "total_cost_basis": float(lt_basis),
                "total_adjustments": float(lt_adjustments),
                "total_gain_or_loss": float(lt_gain),
                "transaction_count": len(long_term),
            },
            "net_short_term_gain_loss": float(st_gain),
            "net_long_term_gain_loss": float(lt_gain),
            "net_capital_gain_loss": float(st_gain + lt_gain),
            "total_transactions": len(self.lines),
        }

    def generate_markdown(self) -> str:
        """Generate Schedule D summary as markdown."""
        data = self.generate()

        lines = []
        lines.append(f"# Schedule D Summary - Tax Year {self.tax_year}")
        lines.append("")

        pi = data["part_i_short_term"]
        lines.append("## Part I - Short-Term Capital Gains and Losses")
        lines.append(f"| Item | Amount |")
        lines.append(f"|------|--------|")
        lines.append(f"| Transactions | {pi['transaction_count']} |")
        lines.append(f"| Total Proceeds | ${pi['total_proceeds']:,.2f} |")
        lines.append(f"| Total Cost Basis | ${pi['total_cost_basis']:,.2f} |")
        lines.append(f"| Adjustments | ${pi['total_adjustments']:,.2f} |")
        lines.append(f"| **Net Short-Term Gain/(Loss)** | **${pi['total_gain_or_loss']:,.2f}** |")
        lines.append("")

        pii = data["part_ii_long_term"]
        lines.append("## Part II - Long-Term Capital Gains and Losses")
        lines.append(f"| Item | Amount |")
        lines.append(f"|------|--------|")
        lines.append(f"| Transactions | {pii['transaction_count']} |")
        lines.append(f"| Total Proceeds | ${pii['total_proceeds']:,.2f} |")
        lines.append(f"| Total Cost Basis | ${pii['total_cost_basis']:,.2f} |")
        lines.append(f"| Adjustments | ${pii['total_adjustments']:,.2f} |")
        lines.append(f"| **Net Long-Term Gain/(Loss)** | **${pii['total_gain_or_loss']:,.2f}** |")
        lines.append("")

        lines.append("## Summary")
        lines.append(f"| | Amount |")
        lines.append(f"|---|--------|")
        lines.append(f"| Net Short-Term | ${data['net_short_term_gain_loss']:,.2f} |")
        lines.append(f"| Net Long-Term | ${data['net_long_term_gain_loss']:,.2f} |")
        lines.append(f"| **Net Capital Gain/(Loss)** | **${data['net_capital_gain_loss']:,.2f}** |")

        return "\n".join(lines)

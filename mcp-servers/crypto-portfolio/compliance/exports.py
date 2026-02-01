"""
Tax Export Formats
==================

Export cryptocurrency tax data in formats required by popular tax tools:
- CPA CSV: Standard format for sharing with accountants
- TurboTax TXF: Tax Exchange Format for TurboTax import
- Koinly CSV: Compatible with Koinly crypto tax software

All exporters accept a list of Form8949Line objects and return string output.
"""

import csv
import io
from datetime import datetime
from typing import List

from .form_8949 import Form8949Line


class CPAExporter:
    """Export in standard CPA-friendly CSV format.

    Produces a clean 11-column CSV that any accountant can work with.
    """

    COLUMNS = [
        "Asset",
        "Date Acquired",
        "Date Sold",
        "Proceeds",
        "Cost Basis",
        "Gain/Loss",
        "Holding Period",
        "Term",
        "Exchange",
        "Transaction ID",
        "Notes",
    ]

    @classmethod
    def export(cls, lines: List[Form8949Line], tax_year: int) -> str:
        """Export Form 8949 lines as CPA-friendly CSV.

        Args:
            lines: Form 8949 line items to export.
            tax_year: Tax year for the report header.

        Returns:
            CSV string with header row and data.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([f"Capital Gains Report - Tax Year {tax_year}"])
        writer.writerow([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
        writer.writerow([])
        writer.writerow(cls.COLUMNS)

        for line in sorted(lines, key=lambda x: x.date_sold):
            days = line.holding_period_days
            term = "Long-term" if line.is_long_term else "Short-term"

            writer.writerow([
                line.asset or line.description,
                line.date_acquired.strftime("%m/%d/%Y"),
                line.date_sold.strftime("%m/%d/%Y"),
                f"{line.proceeds:.2f}",
                f"{line.cost_basis:.2f}",
                f"{line.gain_or_loss:.2f}",
                f"{days} days",
                term,
                line.exchange,
                line.transaction_id,
                line.adjustment_code or "",
            ])

        # Summary section
        writer.writerow([])
        short = [l for l in lines if not l.is_long_term]
        long = [l for l in lines if l.is_long_term]

        if short:
            st_gain = sum(l.gain_or_loss for l in short)
            writer.writerow([f"Short-term net: ${st_gain:,.2f}",
                             f"({len(short)} transactions)"])
        if long:
            lt_gain = sum(l.gain_or_loss for l in long)
            writer.writerow([f"Long-term net: ${lt_gain:,.2f}",
                             f"({len(long)} transactions)"])

        total = sum(l.gain_or_loss for l in lines)
        writer.writerow([f"Total net capital gain/loss: ${total:,.2f}",
                         f"({len(lines)} transactions)"])

        return output.getvalue()


class TurboTaxExporter:
    """Export in TurboTax TXF (Tax Exchange Format).

    TXF is a structured text format used by TurboTax and other tax software.
    Format spec: V042 header, N321 for short-term, N323 for long-term gains.
    """

    @classmethod
    def export(cls, lines: List[Form8949Line], tax_year: int) -> str:
        """Export Form 8949 lines as TurboTax TXF format.

        Args:
            lines: Form 8949 line items to export.
            tax_year: Tax year for the header.

        Returns:
            TXF-formatted string.
        """
        out = []

        # TXF header
        out.append("V042")
        out.append("ACrypto Portfolio Manager")
        out.append(f"D{datetime.now().strftime('%m/%d/%Y')}")
        out.append("^")

        for line in sorted(lines, key=lambda x: x.date_sold):
            # N321 = Short-term, N323 = Long-term
            code = "N323" if line.is_long_term else "N321"
            out.append(f"TD")
            out.append(f"{code}")
            out.append("C1")
            out.append(f"L1")
            out.append(f"P{line.description}")
            out.append(f"D{line.date_acquired.strftime('%m/%d/%Y')}")
            out.append(f"D{line.date_sold.strftime('%m/%d/%Y')}")
            out.append(f"${line.cost_basis:.2f}")
            out.append(f"${line.proceeds:.2f}")
            if line.adjustment_code:
                out.append(f"${line.adjustment_amount:.2f}")
            out.append("^")

        return "\n".join(out)


class KoinlyExporter:
    """Export in Koinly-compatible CSV format.

    Koinly expects a specific CSV format for importing transactions.
    See: https://koinly.io/integrations/csv/
    """

    COLUMNS = [
        "Date",
        "Sent Amount",
        "Sent Currency",
        "Received Amount",
        "Received Currency",
        "Fee Amount",
        "Fee Currency",
        "Net Worth Amount",
        "Net Worth Currency",
        "Label",
        "Description",
        "TxHash",
    ]

    @classmethod
    def export(cls, lines: List[Form8949Line], tax_year: int) -> str:
        """Export Form 8949 lines as Koinly-compatible CSV.

        Note: This converts disposition records into Koinly's send/receive format.
        Each sale is represented as sending the crypto asset and receiving USD.

        Args:
            lines: Form 8949 line items to export.
            tax_year: Tax year for filtering.

        Returns:
            Koinly-formatted CSV string.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(cls.COLUMNS)

        for line in sorted(lines, key=lambda x: x.date_sold):
            # Extract amount and currency from description (e.g. "0.50000000 BTC")
            parts = line.description.strip().split()
            if len(parts) >= 2:
                sent_amount = parts[0]
                sent_currency = parts[1]
            else:
                sent_amount = line.description
                sent_currency = line.asset or "UNKNOWN"

            # Fee is the difference between basis and any adjustment
            fee_amount = ""
            fee_currency = ""

            writer.writerow([
                line.date_sold.strftime("%Y-%m-%d %H:%M:%S UTC"),
                sent_amount,                     # Sent Amount (crypto sold)
                sent_currency,                   # Sent Currency
                f"{line.proceeds:.2f}",          # Received Amount (USD proceeds)
                "USD",                           # Received Currency
                fee_amount,                      # Fee Amount
                fee_currency,                    # Fee Currency
                f"{line.proceeds:.2f}",          # Net Worth Amount
                "USD",                           # Net Worth Currency
                "sell",                          # Label
                f"Sale of {sent_currency}",      # Description
                line.transaction_id or "",       # TxHash
            ])

        return output.getvalue()

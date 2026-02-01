"""
Compliance Module
=================

Tax compliance tools for cryptocurrency portfolio management.

Components:
- form_8949: IRS Form 8949 and Schedule D generation
- exports: CPA CSV, TurboTax TXF, Koinly CSV export formats
- audit_log: Append-only hash-chained audit trail
"""

from .form_8949 import (
    Form8949Box,
    Form8949Line,
    Form8949Generator,
    ScheduleDGenerator,
)
from .exports import CPAExporter, TurboTaxExporter, KoinlyExporter
from .audit_log import AuditEntry, AuditLog

__all__ = [
    "Form8949Box",
    "Form8949Line",
    "Form8949Generator",
    "ScheduleDGenerator",
    "CPAExporter",
    "TurboTaxExporter",
    "KoinlyExporter",
    "AuditEntry",
    "AuditLog",
]

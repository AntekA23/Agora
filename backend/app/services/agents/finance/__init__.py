"""Finance agents module.

This module provides financial agents for:
- Invoice generation with PDF, persistence and automatic numbering
- Cashflow analysis with real calculations and AI insights
"""

from app.services.agents.finance.invoice import (
    InvoiceService,
    generate_invoice_draft,
    validate_invoice_with_ai,
)
from app.services.agents.finance.cashflow import (
    CashflowService,
    analyze_cashflow,
)

__all__ = [
    # Invoice
    "InvoiceService",
    "generate_invoice_draft",
    "validate_invoice_with_ai",
    # Cashflow
    "CashflowService",
    "analyze_cashflow",
]

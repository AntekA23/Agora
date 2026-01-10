"""AI Agents module for Agora platform.

This module provides specialized AI agents for:
- Marketing (Instagram, Copywriter, Campaigns)
- Finance (Invoice, Cashflow)
- HR (Recruiter, Interviewer, Onboarding)
- Sales (Lead Scorer, Proposal Generator)
- Legal (Contract Reviewer)
- Support (Ticket Handler)
- Monitoring (Alerts, Goals)
"""

# Finance agents
from app.services.agents.finance import (
    InvoiceService,
    CashflowService,
    generate_invoice_draft,
    analyze_cashflow,
)

__all__ = [
    # Finance
    "InvoiceService",
    "CashflowService",
    "generate_invoice_draft",
    "analyze_cashflow",
]

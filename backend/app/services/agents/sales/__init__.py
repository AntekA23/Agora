"""Sales Department AI Agents.

Agents for sales tasks:
- Proposal Generator: Creating sales proposals and offers
- CRM Assistant: CRM data analysis and suggestions
- Lead Scorer: Scoring and qualifying leads
"""

from app.services.agents.sales.proposal import generate_sales_proposal
from app.services.agents.sales.lead_scorer import score_lead, analyze_leads_batch
from app.services.agents.sales.crm_assistant import (
    analyze_customer_data,
    suggest_next_actions,
    generate_followup_email,
)

__all__ = [
    "generate_sales_proposal",
    "score_lead",
    "analyze_leads_batch",
    "analyze_customer_data",
    "suggest_next_actions",
    "generate_followup_email",
]

"""Customer Support Department AI Agents.

Agents for support tasks:
- Ticket Handler: Handling and responding to support tickets
- FAQ Generator: Creating FAQ content from tickets
- Sentiment Analyst: Analyzing customer sentiment
"""

from app.services.agents.support.ticket_handler import (
    handle_ticket,
    suggest_response,
    categorize_tickets,
)
from app.services.agents.support.faq_generator import (
    generate_faq_from_tickets,
    generate_help_article,
)
from app.services.agents.support.sentiment_analyst import (
    analyze_sentiment,
    analyze_feedback_batch,
    generate_sentiment_report,
)

__all__ = [
    "handle_ticket",
    "suggest_response",
    "categorize_tickets",
    "generate_faq_from_tickets",
    "generate_help_article",
    "analyze_sentiment",
    "analyze_feedback_batch",
    "generate_sentiment_report",
]

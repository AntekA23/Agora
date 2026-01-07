"""Proactive Monitoring Agents.

Automated agents that monitor various business metrics and generate alerts:
- Cashflow Monitor: Alerts for low balance, unusual spending
- Invoice Monitor: Reminders for unpaid invoices
- Content Monitor: Alerts when content calendar is empty
- Trend Monitor: Notifications about industry trends
- Review Monitor: Alerts for new customer reviews
"""

from app.services.agents.monitoring.cashflow_monitor import CashflowMonitor
from app.services.agents.monitoring.invoice_monitor import InvoiceMonitor
from app.services.agents.monitoring.content_monitor import ContentMonitor
from app.services.agents.monitoring.trend_monitor import TrendMonitor
from app.services.agents.monitoring.alerts import AlertService, Alert, AlertType, AlertPriority

__all__ = [
    "CashflowMonitor",
    "InvoiceMonitor",
    "ContentMonitor",
    "TrendMonitor",
    "AlertService",
    "Alert",
    "AlertType",
    "AlertPriority",
]

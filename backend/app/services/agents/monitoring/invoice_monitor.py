"""Invoice Monitor - Proactive invoice alerts and reminders."""

from datetime import datetime, timedelta
from typing import Any

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.agents.monitoring.alerts import (
    AlertService,
    AlertType,
    AlertPriority,
)


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.5,
        api_key=settings.OPENAI_API_KEY,
    )


class InvoiceMonitor:
    """Monitor for invoice-related alerts."""

    def __init__(self, db):
        """Initialize with database."""
        self.db = db
        self.alert_service = AlertService(db)

    async def check_invoices(
        self,
        company_id: str,
        invoices: list[dict],
        reminder_days_before: int = 3,
    ) -> list[dict]:
        """Check invoices and generate alerts.

        Args:
            company_id: Company ID
            invoices: List of invoices with due dates and status
                [{"id": "...", "number": "...", "client": "...", "amount": X,
                  "due_date": datetime, "status": "pending/paid/overdue"}]
            reminder_days_before: Days before due date to send reminder

        Returns:
            List of generated alerts
        """
        generated_alerts = []
        today = datetime.utcnow().date()

        for invoice in invoices:
            if invoice.get("status") == "paid":
                continue

            due_date = invoice.get("due_date")
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date).date()
            elif isinstance(due_date, datetime):
                due_date = due_date.date()

            if not due_date:
                continue

            days_until_due = (due_date - today).days
            invoice_id = invoice.get("id", "")
            invoice_number = invoice.get("number", "N/A")
            client = invoice.get("client", "Nieznany klient")
            amount = invoice.get("amount", 0)

            # Overdue invoices
            if days_until_due < 0:
                days_overdue = abs(days_until_due)
                priority = AlertPriority.URGENT if days_overdue > 14 else (
                    AlertPriority.HIGH if days_overdue > 7 else AlertPriority.MEDIUM
                )

                alert = await self.alert_service.create_alert(
                    company_id=company_id,
                    alert_type=AlertType.INVOICE_OVERDUE,
                    priority=priority,
                    title=f"Faktura przeterminowana: {invoice_number}",
                    message=f"Faktura {invoice_number} dla {client} na kwotę "
                            f"{amount:,.2f} PLN jest przeterminowana o {days_overdue} dni.",
                    data={
                        "invoice_id": invoice_id,
                        "invoice_number": invoice_number,
                        "client": client,
                        "amount": amount,
                        "due_date": str(due_date),
                        "days_overdue": days_overdue,
                    },
                    action_url=f"/dashboard/finance/invoices/{invoice_id}",
                    action_label="Zobacz fakturę",
                    suggested_actions=[
                        "Wyślij przypomnienie do klienta",
                        "Zadzwoń w sprawie płatności",
                        "Rozważ naliczenie odsetek za zwłokę",
                    ],
                    source_monitor="invoice_monitor",
                    source_entity_id=invoice_id,
                )
                generated_alerts.append(alert.model_dump())

            # Due soon
            elif days_until_due <= reminder_days_before:
                alert = await self.alert_service.create_alert(
                    company_id=company_id,
                    alert_type=AlertType.INVOICE_DUE_SOON,
                    priority=AlertPriority.MEDIUM,
                    title=f"Faktura płatna wkrótce: {invoice_number}",
                    message=f"Faktura {invoice_number} dla {client} na kwotę "
                            f"{amount:,.2f} PLN jest płatna za {days_until_due} dni.",
                    data={
                        "invoice_id": invoice_id,
                        "invoice_number": invoice_number,
                        "client": client,
                        "amount": amount,
                        "due_date": str(due_date),
                        "days_until_due": days_until_due,
                    },
                    action_url=f"/dashboard/finance/invoices/{invoice_id}",
                    action_label="Zobacz fakturę",
                    suggested_actions=[
                        "Wyślij grzeczne przypomnienie do klienta",
                        "Sprawdź status płatności",
                    ],
                    source_monitor="invoice_monitor",
                    source_entity_id=invoice_id,
                )
                generated_alerts.append(alert.model_dump())

        return generated_alerts

    async def generate_payment_reminder(
        self,
        invoice_data: dict,
        reminder_type: str = "friendly",
        company_name: str = "",
    ) -> dict[str, Any]:
        """Generate a payment reminder email.

        Args:
            invoice_data: Invoice details
            reminder_type: friendly, formal, final
            company_name: Your company name

        Returns:
            Dictionary with reminder email content
        """
        llm = _get_llm()

        reminder_writer = Agent(
            role="Payment Reminder Specialist",
            goal="Pisać skuteczne, ale uprzejme przypomnienia o płatnościach",
            backstory="""Jesteś specjalistą od windykacji polubownej.
            Piszesz przypomnienia, które są stanowcze, ale zachowują
            dobre relacje z klientem. Piszesz po polsku.""",
            tools=[],
            llm=llm,
            verbose=False,
        )

        type_instructions = {
            "friendly": "Przyjazne, pierwsze przypomnienie. Zakładamy, że to przeoczenie.",
            "formal": "Formalne przypomnienie. Drugie przypomnienie, bardziej stanowcze.",
            "final": "Ostateczne wezwanie przed podjęciem kroków prawnych.",
        }

        instruction = type_instructions.get(reminder_type, type_instructions["friendly"])

        task = Task(
            description=f"""
            Napisz przypomnienie o płatności:

            DANE FAKTURY:
            - Numer: {invoice_data.get('number', 'N/A')}
            - Klient: {invoice_data.get('client', 'N/A')}
            - Kwota: {invoice_data.get('amount', 0):,.2f} PLN
            - Termin płatności: {invoice_data.get('due_date', 'N/A')}
            - Dni po terminie: {invoice_data.get('days_overdue', 0)}

            NASZA FIRMA: {company_name or "[Nazwa firmy]"}

            TYP PRZYPOMNIENIA: {reminder_type}
            INSTRUKCJE: {instruction}

            Zwróć w formacie JSON:
            {{
                "subject": "temat emaila",
                "greeting": "powitanie",
                "body": "treść główna",
                "payment_details": "szczegóły płatności",
                "closing": "zakończenie",
                "full_email": "pełna treść emaila",
                "sms_version": "krótka wersja SMS (max 160 znaków)"
            }}
            """,
            agent=reminder_writer,
            expected_output="Payment reminder in JSON format",
        )

        crew = Crew(
            agents=[reminder_writer],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()

        import json
        import re

        result_text = str(result)
        json_match = re.search(r'\{[\s\S]*\}', result_text)

        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return {"success": True, "reminder": parsed}
            except json.JSONDecodeError:
                pass

        return {"success": True, "reminder": {"full_email": result_text}}

    async def get_invoice_summary(
        self,
        company_id: str,
        invoices: list[dict],
    ) -> dict[str, Any]:
        """Get summary of invoice status.

        Args:
            company_id: Company ID
            invoices: List of invoices

        Returns:
            Dictionary with invoice summary
        """
        today = datetime.utcnow().date()

        summary = {
            "total_invoices": len(invoices),
            "paid": 0,
            "pending": 0,
            "overdue": 0,
            "total_amount": 0,
            "paid_amount": 0,
            "pending_amount": 0,
            "overdue_amount": 0,
            "oldest_overdue_days": 0,
            "invoices_by_status": [],
        }

        for invoice in invoices:
            amount = invoice.get("amount", 0)
            status = invoice.get("status", "pending")
            summary["total_amount"] += amount

            if status == "paid":
                summary["paid"] += 1
                summary["paid_amount"] += amount
            else:
                due_date = invoice.get("due_date")
                if isinstance(due_date, str):
                    due_date = datetime.fromisoformat(due_date).date()
                elif isinstance(due_date, datetime):
                    due_date = due_date.date()

                if due_date and due_date < today:
                    summary["overdue"] += 1
                    summary["overdue_amount"] += amount
                    days_overdue = (today - due_date).days
                    if days_overdue > summary["oldest_overdue_days"]:
                        summary["oldest_overdue_days"] = days_overdue
                else:
                    summary["pending"] += 1
                    summary["pending_amount"] += amount

        return summary

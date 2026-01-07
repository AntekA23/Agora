"""Cashflow Monitor - Proactive cashflow alerts."""

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
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY,
    )


class CashflowMonitor:
    """Monitor for cashflow-related alerts."""

    def __init__(self, db):
        """Initialize with database."""
        self.db = db
        self.alert_service = AlertService(db)

    async def check_company(
        self,
        company_id: str,
        current_balance: float,
        monthly_expenses: float,
        low_balance_threshold: float | None = None,
        recent_transactions: list[dict] | None = None,
    ) -> list[dict]:
        """Check cashflow health for a company and generate alerts.

        Args:
            company_id: Company ID
            current_balance: Current account balance
            monthly_expenses: Average monthly expenses
            low_balance_threshold: Custom threshold (default: 2x monthly expenses)
            recent_transactions: Recent transactions for analysis

        Returns:
            List of generated alerts
        """
        generated_alerts = []

        # Calculate threshold (default: 2 months of expenses)
        threshold = low_balance_threshold or (monthly_expenses * 2)

        # Check for low balance
        if current_balance < threshold:
            months_runway = current_balance / monthly_expenses if monthly_expenses > 0 else 0

            priority = AlertPriority.URGENT if months_runway < 1 else (
                AlertPriority.HIGH if months_runway < 2 else AlertPriority.MEDIUM
            )

            alert = await self.alert_service.create_alert(
                company_id=company_id,
                alert_type=AlertType.CASHFLOW_LOW_BALANCE,
                priority=priority,
                title="Niski stan konta",
                message=f"Obecne saldo ({current_balance:,.2f} PLN) jest poniżej "
                        f"zalecanego progu ({threshold:,.2f} PLN). "
                        f"Wystarczy na około {months_runway:.1f} miesięcy.",
                data={
                    "current_balance": current_balance,
                    "threshold": threshold,
                    "monthly_expenses": monthly_expenses,
                    "months_runway": round(months_runway, 1),
                },
                action_url="/dashboard/finance",
                action_label="Zobacz szczegóły",
                suggested_actions=[
                    "Przejrzyj zaległe faktury do inkasa",
                    "Rozważ przyspieszenie płatności od klientów",
                    "Sprawdź możliwości redukcji kosztów",
                ],
                source_monitor="cashflow_monitor",
            )
            generated_alerts.append(alert.model_dump())

        # Analyze recent transactions for unusual spending
        if recent_transactions:
            analysis = await self._analyze_transactions(
                company_id=company_id,
                transactions=recent_transactions,
                monthly_average=monthly_expenses,
            )
            if analysis:
                generated_alerts.extend(analysis)

        return generated_alerts

    async def _analyze_transactions(
        self,
        company_id: str,
        transactions: list[dict],
        monthly_average: float,
    ) -> list[dict]:
        """Analyze transactions for unusual patterns."""
        alerts = []

        # Calculate recent spending
        recent_expenses = sum(
            t.get("amount", 0) for t in transactions
            if t.get("type") == "expense"
        )

        # Check if spending is unusually high (>150% of average)
        if recent_expenses > monthly_average * 1.5:
            alert = await self.alert_service.create_alert(
                company_id=company_id,
                alert_type=AlertType.CASHFLOW_UNUSUAL_SPENDING,
                priority=AlertPriority.MEDIUM,
                title="Nietypowo wysokie wydatki",
                message=f"Ostatnie wydatki ({recent_expenses:,.2f} PLN) są znacznie "
                        f"wyższe niż średnia miesięczna ({monthly_average:,.2f} PLN).",
                data={
                    "recent_expenses": recent_expenses,
                    "monthly_average": monthly_average,
                    "difference_percent": round((recent_expenses / monthly_average - 1) * 100, 1),
                },
                action_url="/dashboard/finance/transactions",
                action_label="Przejrzyj transakcje",
                suggested_actions=[
                    "Sprawdź największe pozycje wydatków",
                    "Zweryfikuj, czy wszystkie transakcje są prawidłowe",
                ],
                source_monitor="cashflow_monitor",
            )
            alerts.append(alert.model_dump())

        # Check for positive trend (income > expenses)
        recent_income = sum(
            t.get("amount", 0) for t in transactions
            if t.get("type") == "income"
        )

        if recent_income > recent_expenses * 1.3:
            alert = await self.alert_service.create_alert(
                company_id=company_id,
                alert_type=AlertType.CASHFLOW_POSITIVE_TREND,
                priority=AlertPriority.LOW,
                title="Pozytywny trend cashflow",
                message=f"Gratulacje! Ostatnie przychody ({recent_income:,.2f} PLN) "
                        f"przewyższają wydatki ({recent_expenses:,.2f} PLN).",
                data={
                    "recent_income": recent_income,
                    "recent_expenses": recent_expenses,
                    "net_cashflow": recent_income - recent_expenses,
                },
                action_url="/dashboard/finance",
                action_label="Zobacz szczegóły",
                suggested_actions=[
                    "Rozważ utworzenie rezerwy finansowej",
                    "Sprawdź możliwości inwestycji w rozwój",
                ],
                source_monitor="cashflow_monitor",
            )
            alerts.append(alert.model_dump())

        return alerts

    async def generate_cashflow_insights(
        self,
        company_id: str,
        financial_data: dict,
    ) -> dict[str, Any]:
        """Generate AI-powered cashflow insights.

        Args:
            company_id: Company ID
            financial_data: Dictionary with financial data

        Returns:
            Dictionary with insights and recommendations
        """
        llm = _get_llm()

        analyst = Agent(
            role="Financial Analyst",
            goal="Analizować cashflow i dostarczać praktyczne rekomendacje",
            backstory="""Jesteś doświadczonym analitykiem finansowym dla MŚP.
            Potrafisz szybko ocenić sytuację finansową i zaproponować działania.""",
            tools=[],
            llm=llm,
            verbose=False,
        )

        task = Task(
            description=f"""
            Przeanalizuj dane finansowe firmy i dostarcz insights:

            DANE FINANSOWE:
            - Saldo: {financial_data.get('balance', 'N/A')} PLN
            - Przychody (ostatni miesiąc): {financial_data.get('income', 'N/A')} PLN
            - Wydatki (ostatni miesiąc): {financial_data.get('expenses', 'N/A')} PLN
            - Zaległe faktury (do zapłaty): {financial_data.get('payables', 'N/A')} PLN
            - Zaległe faktury (do inkasa): {financial_data.get('receivables', 'N/A')} PLN

            Zwróć w formacie JSON:
            {{
                "health_score": 0-100,
                "status": "healthy/warning/critical",
                "runway_months": X,
                "key_insights": ["insight 1", "insight 2"],
                "risks": ["risk 1", "risk 2"],
                "opportunities": ["opportunity 1"],
                "recommendations": [
                    {{
                        "action": "co zrobić",
                        "priority": "high/medium/low",
                        "expected_impact": "oczekiwany efekt"
                    }}
                ],
                "summary": "podsumowanie 2-3 zdania"
            }}
            """,
            agent=analyst,
            expected_output="Cashflow insights in JSON format",
        )

        crew = Crew(
            agents=[analyst],
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
                return {"success": True, "insights": parsed}
            except json.JSONDecodeError:
                pass

        return {"success": True, "insights": {"raw_content": result_text}}

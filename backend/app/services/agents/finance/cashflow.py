"""Cashflow Agent - Complete cashflow analysis with calculations, AI insights and PDF reports.

This module provides:
- Real financial calculations (not just AI research)
- Category breakdown and metrics
- Health score calculation
- AI-powered insights and recommendations
- PDF report generation
- Persistence to MongoDB
"""

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
import json
import re

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.models.invoice import CashflowRecord, CashflowReport
from app.schemas.finance import (
    CashflowItem,
    CashflowMetrics,
    CashflowRecommendation,
    CashflowResult,
    CashflowTaskInput,
    CategoryBreakdown,
)
from app.services.agents.tools.pdf_generator import pdf_generator
from app.services.agents.tools.calculator import CashflowCalculatorTool
from app.services.agents.tools.web_search import TavilySearchTool, TavilyMarketDataTool


class CashflowService:
    """Service for cashflow analysis and reporting."""

    def __init__(self, db: AsyncIOMotorDatabase | None = None):
        """Initialize with optional database connection."""
        self.db = db
        self.calculator = CashflowCalculatorTool()

    def calculate_metrics(
        self,
        income: list[CashflowItem],
        expenses: list[CashflowItem],
        period: str = "miesiac",
    ) -> CashflowMetrics:
        """Calculate all cashflow metrics from raw data."""
        metrics = CashflowMetrics()

        # Basic totals
        total_income = Decimal("0")
        total_expenses = Decimal("0")

        for item in income:
            total_income += Decimal(str(item.amount))

        for item in expenses:
            total_expenses += Decimal(str(item.amount))

        metrics.total_income = float(total_income.quantize(Decimal("0.01"), ROUND_HALF_UP))
        metrics.total_expenses = float(total_expenses.quantize(Decimal("0.01"), ROUND_HALF_UP))
        metrics.balance = float((total_income - total_expenses).quantize(Decimal("0.01"), ROUND_HALF_UP))

        # Ratios
        if total_income > 0:
            metrics.expense_to_income_ratio = float(
                (total_expenses / total_income).quantize(Decimal("0.01"), ROUND_HALF_UP)
            )
            savings_rate = ((total_income - total_expenses) / total_income * 100)
            metrics.savings_rate = float(savings_rate.quantize(Decimal("0.01"), ROUND_HALF_UP))
        else:
            metrics.expense_to_income_ratio = 0.0
            metrics.savings_rate = 0.0

        # Runway calculation (how many months can company survive)
        if total_expenses > 0:
            # Assume balance is current capital
            if metrics.balance > 0:
                metrics.months_runway = float(
                    (Decimal(str(metrics.balance)) / total_expenses).quantize(Decimal("0.1"), ROUND_HALF_UP)
                )
            else:
                metrics.months_runway = 0.0
        else:
            metrics.months_runway = 12.0  # No expenses = infinite runway, cap at 12

        # Health score calculation (0-100)
        health_score = 50  # Start at neutral

        # Balance impact (+/- 20 points)
        if metrics.balance > 0:
            balance_ratio = min(metrics.balance / max(metrics.total_income, 1), 0.5)
            health_score += int(balance_ratio * 40)
        else:
            deficit_ratio = min(abs(metrics.balance) / max(metrics.total_income, 1), 0.5)
            health_score -= int(deficit_ratio * 40)

        # Savings rate impact (+/- 15 points)
        if metrics.savings_rate > 20:
            health_score += 15
        elif metrics.savings_rate > 10:
            health_score += 10
        elif metrics.savings_rate > 0:
            health_score += 5
        elif metrics.savings_rate < -10:
            health_score -= 15
        elif metrics.savings_rate < 0:
            health_score -= 10

        # Runway impact (+/- 15 points)
        if metrics.months_runway >= 6:
            health_score += 15
        elif metrics.months_runway >= 3:
            health_score += 10
        elif metrics.months_runway >= 1:
            health_score += 0
        else:
            health_score -= 15

        # Clamp to 0-100
        metrics.health_score = max(0, min(100, health_score))

        # Health status
        if metrics.health_score >= 70:
            metrics.health_status = "healthy"
        elif metrics.health_score >= 40:
            metrics.health_status = "warning"
        else:
            metrics.health_status = "critical"

        return metrics

    def calculate_category_breakdown(
        self, items: list[CashflowItem], total: float
    ) -> list[CategoryBreakdown]:
        """Calculate breakdown by category."""
        by_category: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"amount": Decimal("0"), "count": 0}
        )

        for item in items:
            category = item.category or "inne"
            by_category[category]["amount"] += Decimal(str(item.amount))
            by_category[category]["count"] += 1

        breakdowns = []
        total_decimal = Decimal(str(total)) if total > 0 else Decimal("1")

        for category, data in sorted(
            by_category.items(), key=lambda x: x[1]["amount"], reverse=True
        ):
            amount = float(data["amount"].quantize(Decimal("0.01"), ROUND_HALF_UP))
            percentage = float(
                (data["amount"] / total_decimal * 100).quantize(Decimal("0.1"), ROUND_HALF_UP)
            )
            breakdowns.append(
                CategoryBreakdown(
                    category=category,
                    amount=amount,
                    percentage=percentage,
                    count=data["count"],
                )
            )

        return breakdowns

    async def generate_ai_analysis(
        self,
        metrics: CashflowMetrics,
        income_breakdown: list[CategoryBreakdown],
        expenses_breakdown: list[CategoryBreakdown],
        period: str,
        industry: str = "",
    ) -> dict[str, Any]:
        """Generate AI-powered analysis and recommendations."""
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.4,
        )

        # Initialize tools for market research
        search_tool = TavilySearchTool()
        market_tool = TavilyMarketDataTool()

        # Market Researcher Agent
        researcher = Agent(
            role="Market Research Analyst",
            goal="Znajdz benchmarki branzowe i dane porownawcze dla analizy cashflow",
            backstory="""Jestes analitykiem rynkowym specjalizujacym sie w malych firmach w Polsce.
            Szukasz benchmarkow i danych porownawczych dla analizy finansowej.""",
            llm=llm,
            tools=[search_tool, market_tool],
            verbose=False,
        )

        # Financial Analyst Agent
        analyst = Agent(
            role="Financial Analyst",
            goal="Analizuj dane finansowe i przygotuj praktyczne rekomendacje",
            backstory="""Jestes doswiadczonym analitykiem finansowym dla MŚP w Polsce.
            Potrafisz wyciagac wnioski z danych i dawac konkretne, wykonalne rekomendacje.
            Twoje analizy sa zwiezle i praktyczne.""",
            llm=llm,
            verbose=False,
        )

        # Format data for prompts
        income_text = "\n".join([
            f"- {b.category}: {b.amount:.2f} PLN ({b.percentage:.1f}%)"
            for b in income_breakdown
        ]) or "Brak danych"

        expenses_text = "\n".join([
            f"- {b.category}: {b.amount:.2f} PLN ({b.percentage:.1f}%)"
            for b in expenses_breakdown
        ]) or "Brak danych"

        top_expense_categories = [b.category for b in expenses_breakdown[:3]]

        # Task 1: Research
        research_task = Task(
            description=f"""Przeprowadz krotki research rynkowy:

BRANZA: {industry or 'mala firma / MŚP'}
GLOWNE KATEGORIE WYDATKOW: {', '.join(top_expense_categories)}

Znajdz:
1. Typowe proporcje wydatkow do przychodow dla malych firm w Polsce
2. 2-3 konkretne sposoby optymalizacji wydatkow w kategoriach: {', '.join(top_expense_categories)}

Zwroc krotkie, konkretne informacje.""",
            expected_output="Krotki research z benchmarkami i sposobami optymalizacji",
            agent=researcher,
        )

        # Task 2: Analysis
        analysis_task = Task(
            description=f"""Przeanalizuj cashflow i przygotuj raport:

METRYKI:
- Przychody: {metrics.total_income:.2f} PLN
- Wydatki: {metrics.total_expenses:.2f} PLN
- Bilans: {metrics.balance:.2f} PLN
- Wskaznik wydatkow do przychodow: {metrics.expense_to_income_ratio:.2f}
- Stopa oszczednosci: {metrics.savings_rate:.1f}%
- Runway: {metrics.months_runway:.1f} miesiecy
- Health Score: {metrics.health_score}/100 ({metrics.health_status})
- Okres: {period}

PRZYCHODY WG KATEGORII:
{income_text}

WYDATKI WG KATEGORII:
{expenses_text}

Na podstawie danych i researchu, przygotuj odpowiedz w formacie JSON:
{{
    "summary": "2-3 zdania podsumowania sytuacji finansowej",
    "analysis": "Szczegolowa analiza 3-5 zdan",
    "recommendations": [
        {{
            "action": "konkretne dzialanie do podjecia",
            "priority": "high/medium/low",
            "expected_impact": "oczekiwany efekt",
            "category": "cost_reduction/income_increase/risk_mitigation"
        }}
    ],
    "warnings": ["lista ostrzezen jesli sa"],
    "opportunities": ["lista szans jesli sa"],
    "benchmark_comparison": "porownanie z benchmarkami branzowymi"
}}

Podaj 5-7 konkretnych rekomendacji. Kazda musi byc wykonalna i praktyczna.""",
            expected_output="JSON z analiza i rekomendacjami",
            agent=analyst,
            context=[research_task],
        )

        crew = Crew(
            agents=[researcher, analyst],
            tasks=[research_task, analysis_task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()
        result_text = str(result)

        # Parse JSON from result
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback if parsing fails
        return {
            "summary": "Analiza cashflow zostala przeprowadzona.",
            "analysis": result_text[:500],
            "recommendations": [],
            "warnings": [],
            "opportunities": [],
            "benchmark_comparison": "",
        }

    async def analyze_cashflow(
        self,
        input_data: CashflowTaskInput,
        company_id: str | None = None,
        industry: str = "",
    ) -> CashflowResult:
        """Perform complete cashflow analysis.

        Args:
            input_data: Cashflow data (income and expenses)
            company_id: Optional company ID for persistence
            industry: Optional industry for benchmarks

        Returns:
            CashflowResult with metrics, analysis and recommendations
        """
        result = CashflowResult()

        try:
            # 1. Calculate metrics
            metrics = self.calculate_metrics(
                input_data.income,
                input_data.expenses,
                input_data.period,
            )
            result.metrics = metrics

            # 2. Calculate category breakdowns
            result.income_by_category = self.calculate_category_breakdown(
                input_data.income, metrics.total_income
            )
            result.expenses_by_category = self.calculate_category_breakdown(
                input_data.expenses, metrics.total_expenses
            )

            # 3. Set period info
            result.period = input_data.period
            now = datetime.utcnow()
            if input_data.period == "miesiac":
                result.period_start = (now.replace(day=1)).strftime("%Y-%m-%d")
                result.period_end = now.strftime("%Y-%m-%d")
            elif input_data.period == "kwartal":
                quarter_start_month = ((now.month - 1) // 3) * 3 + 1
                result.period_start = now.replace(month=quarter_start_month, day=1).strftime("%Y-%m-%d")
                result.period_end = now.strftime("%Y-%m-%d")
            else:
                result.period_start = now.replace(month=1, day=1).strftime("%Y-%m-%d")
                result.period_end = now.strftime("%Y-%m-%d")

            # 4. Generate AI analysis if requested
            if input_data.include_analysis or input_data.include_recommendations:
                ai_analysis = await self.generate_ai_analysis(
                    metrics,
                    result.income_by_category,
                    result.expenses_by_category,
                    input_data.period,
                    industry,
                )

                result.summary = ai_analysis.get("summary", "")
                result.analysis = ai_analysis.get("analysis", "")
                result.benchmark_comparison = ai_analysis.get("benchmark_comparison", "")
                result.warnings = ai_analysis.get("warnings", [])
                result.opportunities = ai_analysis.get("opportunities", [])

                # Parse recommendations
                raw_recommendations = ai_analysis.get("recommendations", [])
                for rec in raw_recommendations:
                    if isinstance(rec, dict):
                        result.recommendations.append(
                            CashflowRecommendation(
                                action=rec.get("action", ""),
                                priority=rec.get("priority", "medium"),
                                expected_impact=rec.get("expected_impact", ""),
                                category=rec.get("category", ""),
                            )
                        )

            # 5. Generate PDF if requested
            if input_data.generate_pdf:
                try:
                    report_content = self._format_report_content(result)
                    pdf_bytes = pdf_generator.generate_report_pdf(
                        title=f"Analiza Cashflow - {input_data.period.capitalize()}",
                        subtitle=f"Wygenerowano: {now.strftime('%d.%m.%Y')}",
                        content=report_content,
                        total_income=metrics.total_income,
                        total_expenses=metrics.total_expenses,
                        balance=metrics.balance,
                        show_summary=True,
                    )
                    result.pdf_base64 = pdf_generator.pdf_to_base64(pdf_bytes)
                    result.pdf_generated = True
                except Exception:
                    result.pdf_generated = False

            # 6. Save to database if requested
            if input_data.save_to_db and self.db and company_id:
                report = CashflowReport(
                    company_id=company_id,
                    period=input_data.period,
                    period_start=datetime.strptime(result.period_start, "%Y-%m-%d"),
                    period_end=datetime.strptime(result.period_end, "%Y-%m-%d"),
                    total_income=metrics.total_income,
                    total_expenses=metrics.total_expenses,
                    balance=metrics.balance,
                    income_by_category={b.category: b.amount for b in result.income_by_category},
                    expenses_by_category={b.category: b.amount for b in result.expenses_by_category},
                    analysis_content=result.analysis,
                    recommendations=[r.action for r in result.recommendations],
                    warnings=result.warnings,
                    health_score=metrics.health_score,
                    pdf_generated=result.pdf_generated,
                    pdf_base64=result.pdf_base64 if result.pdf_generated else "",
                )

                report_dict = report.model_dump(by_alias=True, exclude={"id"})
                insert_result = await self.db.cashflow_reports.insert_one(report_dict)
                result.report_id = str(insert_result.inserted_id)

            result.success = True
            return result

        except Exception as e:
            result.success = False
            result.error = f"Blad analizy cashflow: {e!s}"
            return result

    def _format_report_content(self, result: CashflowResult) -> str:
        """Format report content for PDF."""
        lines = []

        # Summary
        if result.summary:
            lines.append("PODSUMOWANIE")
            lines.append(result.summary)
            lines.append("")

        # Metrics
        lines.append("WSKAZNIKI")
        lines.append(f"- Health Score: {result.metrics.health_score}/100 ({result.metrics.health_status})")
        lines.append(f"- Stopa oszczednosci: {result.metrics.savings_rate:.1f}%")
        lines.append(f"- Runway: {result.metrics.months_runway:.1f} miesiecy")
        lines.append("")

        # Income breakdown
        if result.income_by_category:
            lines.append("PRZYCHODY WG KATEGORII")
            for b in result.income_by_category:
                lines.append(f"- {b.category}: {b.amount:.2f} PLN ({b.percentage:.1f}%)")
            lines.append("")

        # Expenses breakdown
        if result.expenses_by_category:
            lines.append("WYDATKI WG KATEGORII")
            for b in result.expenses_by_category:
                lines.append(f"- {b.category}: {b.amount:.2f} PLN ({b.percentage:.1f}%)")
            lines.append("")

        # Analysis
        if result.analysis:
            lines.append("ANALIZA")
            lines.append(result.analysis)
            lines.append("")

        # Recommendations
        if result.recommendations:
            lines.append("REKOMENDACJE")
            for i, rec in enumerate(result.recommendations, 1):
                priority_pl = {"high": "wysoki", "medium": "sredni", "low": "niski"}.get(rec.priority, rec.priority)
                lines.append(f"{i}. [{priority_pl}] {rec.action}")
                if rec.expected_impact:
                    lines.append(f"   Oczekiwany efekt: {rec.expected_impact}")
            lines.append("")

        # Warnings
        if result.warnings:
            lines.append("OSTRZEZENIA")
            for warning in result.warnings:
                lines.append(f"! {warning}")
            lines.append("")

        # Opportunities
        if result.opportunities:
            lines.append("SZANSE")
            for opp in result.opportunities:
                lines.append(f"+ {opp}")

        return "\n".join(lines)


# =============================================================================
# LEGACY FUNCTION (for backward compatibility)
# =============================================================================


async def analyze_cashflow(
    income: list[dict],
    expenses: list[dict],
    period: str = "miesiac",
    language: str = "pl",
    industry: str = "",
) -> dict:
    """Legacy function - analyze cashflow.

    DEPRECATED: Use CashflowService.analyze_cashflow() instead for full functionality.
    """
    # Convert to new format
    income_items = [
        CashflowItem(
            description=item.get("description", "Przychod"),
            amount=item.get("amount", 0),
            date=item.get("date", ""),
            category=item.get("category", ""),
        )
        for item in income
    ]

    expense_items = [
        CashflowItem(
            description=item.get("description", "Wydatek"),
            amount=item.get("amount", 0),
            date=item.get("date", ""),
            category=item.get("category", ""),
        )
        for item in expenses
    ]

    input_data = CashflowTaskInput(
        income=income_items,
        expenses=expense_items,
        period=period,
        include_analysis=True,
        include_recommendations=True,
        generate_pdf=False,
        save_to_db=False,
    )

    service = CashflowService()
    result = await service.analyze_cashflow(input_data, industry=industry)

    # Convert to legacy format
    return {
        "content": result.analysis or result.summary,
        "period": result.period,
        "total_income": result.metrics.total_income,
        "total_expenses": result.metrics.total_expenses,
        "balance": result.metrics.balance,
        "health_score": result.metrics.health_score,
        "health_status": result.metrics.health_status,
        "recommendations": [r.action for r in result.recommendations],
        "warnings": result.warnings,
        "used_tavily": True,
        "industry": industry,
    }

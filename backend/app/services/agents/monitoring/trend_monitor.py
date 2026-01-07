"""Trend Monitor - Proactive industry trend alerts."""

from datetime import datetime, timedelta
from typing import Any

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.agents.tools.web_search import search_tool
from app.services.agents.monitoring.alerts import (
    AlertService,
    AlertType,
    AlertPriority,
)


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.6,
        api_key=settings.OPENAI_API_KEY,
    )


class TrendMonitor:
    """Monitor for industry trends and opportunities."""

    def __init__(self, db):
        """Initialize with database."""
        self.db = db
        self.alert_service = AlertService(db)

    async def scan_industry_trends(
        self,
        company_id: str,
        industry: str,
        keywords: list[str] | None = None,
        competitors: list[str] | None = None,
    ) -> list[dict]:
        """Scan for industry trends and generate alerts.

        Args:
            company_id: Company ID
            industry: Company industry
            keywords: Additional keywords to monitor
            competitors: Competitor names to monitor

        Returns:
            List of generated alerts
        """
        if not settings.TAVILY_API_KEY:
            return []

        generated_alerts = []
        llm = _get_llm()

        trend_analyst = Agent(
            role="Trend Analyst",
            goal="Identyfikować istotne trendy i możliwości biznesowe",
            backstory="""Jesteś analitykiem trendów rynkowych specjalizującym się
            w polskim rynku. Wyszukujesz informacje i identyfikujesz trendy,
            które mogą wpłynąć na biznes.""",
            tools=[search_tool],
            llm=llm,
            verbose=False,
        )

        keywords_text = ", ".join(keywords or [])
        competitors_text = ", ".join(competitors or [])

        task = Task(
            description=f"""
            Przeszukaj internet w poszukiwaniu trendów i nowości:

            BRANŻA: {industry}
            DODATKOWE SŁOWA KLUCZOWE: {keywords_text or "brak"}
            KONKURENCI DO MONITOROWANIA: {competitors_text or "brak"}

            WYSZUKAJ:
            1. Nowe trendy w branży {industry} w Polsce
            2. Zmiany regulacyjne lub prawne
            3. Działania konkurencji (jeśli podano)
            4. Nowe technologie lub rozwiązania
            5. Zmiany w zachowaniach konsumentów

            Zwróć w formacie JSON:
            {{
                "trends": [
                    {{
                        "title": "tytuł trendu",
                        "description": "opis",
                        "relevance": "high/medium/low",
                        "urgency": "immediate/soon/long_term",
                        "opportunity_type": "growth/cost_saving/competitive/regulatory",
                        "recommended_action": "sugerowana reakcja",
                        "source": "źródło informacji"
                    }}
                ],
                "competitor_news": [
                    {{
                        "competitor": "nazwa",
                        "news": "co zrobili",
                        "impact": "potencjalny wpływ na nas",
                        "response_suggestion": "sugestia reakcji"
                    }}
                ],
                "opportunities": [
                    {{
                        "opportunity": "opis szansy",
                        "potential_impact": "potencjalny wpływ",
                        "time_sensitivity": "high/medium/low",
                        "resources_needed": "szacowane zasoby"
                    }}
                ],
                "risks": [
                    {{
                        "risk": "opis ryzyka",
                        "severity": "high/medium/low",
                        "mitigation": "jak się zabezpieczyć"
                    }}
                ],
                "summary": "podsumowanie 2-3 zdania"
            }}
            """,
            agent=trend_analyst,
            expected_output="Trend analysis in JSON format",
        )

        crew = Crew(
            agents=[trend_analyst],
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

                # Create alerts for high-relevance trends
                for trend in parsed.get("trends", []):
                    if trend.get("relevance") == "high":
                        alert = await self.alert_service.create_alert(
                            company_id=company_id,
                            alert_type=AlertType.TREND_NEW_INDUSTRY,
                            priority=AlertPriority.MEDIUM if trend.get("urgency") != "immediate" else AlertPriority.HIGH,
                            title=f"Nowy trend: {trend.get('title', 'Nieznany')}",
                            message=trend.get("description", "")[:200],
                            data=trend,
                            suggested_actions=[trend.get("recommended_action", "Przeanalizuj trend")],
                            source_monitor="trend_monitor",
                        )
                        generated_alerts.append(alert.model_dump())

                # Create alerts for competitor news
                for news in parsed.get("competitor_news", []):
                    alert = await self.alert_service.create_alert(
                        company_id=company_id,
                        alert_type=AlertType.TREND_COMPETITOR_ACTION,
                        priority=AlertPriority.MEDIUM,
                        title=f"Aktywność konkurenta: {news.get('competitor', 'Nieznany')}",
                        message=news.get("news", "")[:200],
                        data=news,
                        suggested_actions=[news.get("response_suggestion", "Monitoruj sytuację")],
                        source_monitor="trend_monitor",
                    )
                    generated_alerts.append(alert.model_dump())

                # Create alerts for time-sensitive opportunities
                for opp in parsed.get("opportunities", []):
                    if opp.get("time_sensitivity") == "high":
                        alert = await self.alert_service.create_alert(
                            company_id=company_id,
                            alert_type=AlertType.TREND_OPPORTUNITY,
                            priority=AlertPriority.HIGH,
                            title="Pilna szansa biznesowa",
                            message=opp.get("opportunity", "")[:200],
                            data=opp,
                            source_monitor="trend_monitor",
                        )
                        generated_alerts.append(alert.model_dump())

                return generated_alerts

            except json.JSONDecodeError:
                pass

        return generated_alerts

    async def get_trend_report(
        self,
        company_id: str,
        industry: str,
        period: str = "weekly",
    ) -> dict[str, Any]:
        """Generate a comprehensive trend report.

        Args:
            company_id: Company ID
            industry: Company industry
            period: Report period (daily, weekly, monthly)

        Returns:
            Dictionary with trend report
        """
        if not settings.TAVILY_API_KEY:
            return {
                "success": False,
                "error": "Tavily API key not configured for trend monitoring",
            }

        llm = _get_llm()

        reporter = Agent(
            role="Trend Reporter",
            goal="Tworzyć kompleksowe raporty trendów branżowych",
            backstory="""Jesteś analitykiem przygotowującym raporty trendów
            dla zarządu. Wyszukujesz najważniejsze informacje i przedstawiasz
            je w zwięzły sposób z konkretnymi rekomendacjami.""",
            tools=[search_tool],
            llm=llm,
            verbose=False,
        )

        task = Task(
            description=f"""
            Przygotuj raport trendów dla branży: {industry}
            Okres: {period}

            PRZESZUKAJ I UWZGLĘDNIJ:
            1. Najważniejsze wydarzenia w branży
            2. Nowe produkty/usługi konkurencji
            3. Zmiany regulacyjne
            4. Trendy konsumenckie
            5. Innowacje technologiczne

            Zwróć w formacie JSON:
            {{
                "report_title": "Raport Trendów - {industry}",
                "period": "{period}",
                "generated_at": "data",
                "executive_summary": "podsumowanie 3-4 zdania",
                "key_developments": [
                    {{
                        "development": "wydarzenie",
                        "impact": "wpływ na branżę",
                        "our_relevance": "znaczenie dla nas"
                    }}
                ],
                "market_signals": [
                    {{
                        "signal": "sygnał rynkowy",
                        "interpretation": "interpretacja",
                        "confidence": "high/medium/low"
                    }}
                ],
                "action_items": [
                    {{
                        "action": "działanie",
                        "priority": "high/medium/low",
                        "deadline_suggestion": "sugerowany termin"
                    }}
                ],
                "watch_list": ["tematy do dalszego monitorowania"],
                "next_report_focus": ["na co zwrócić uwagę w następnym raporcie"]
            }}
            """,
            agent=reporter,
            expected_output="Trend report in JSON format",
        )

        crew = Crew(
            agents=[reporter],
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
                return {"success": True, "report": parsed}
            except json.JSONDecodeError:
                pass

        return {"success": True, "report": {"raw_content": result_text}}

    async def monitor_keywords(
        self,
        company_id: str,
        keywords: list[str],
        alert_on_mention: bool = True,
    ) -> dict[str, Any]:
        """Monitor specific keywords for mentions.

        Args:
            company_id: Company ID
            keywords: Keywords to monitor
            alert_on_mention: Whether to create alerts

        Returns:
            Dictionary with keyword mentions
        """
        if not settings.TAVILY_API_KEY:
            return {
                "success": False,
                "error": "Tavily API key not configured",
            }

        llm = _get_llm()

        monitor = Agent(
            role="Keyword Monitor",
            goal="Monitorować wzmianki o określonych słowach kluczowych",
            backstory="""Jesteś specjalistą od monitoringu mediów.
            Wyszukujesz wzmianki i analizujesz ich kontekst i sentyment.""",
            tools=[search_tool],
            llm=llm,
            verbose=False,
        )

        keywords_text = ", ".join(keywords)

        task = Task(
            description=f"""
            Wyszukaj najnowsze wzmianki o: {keywords_text}

            Dla każdego słowa kluczowego znajdź:
            1. Ostatnie wzmianki w mediach/internecie
            2. Kontekst wzmianki (pozytywny/negatywny/neutralny)
            3. Źródło i zasięg

            Zwróć w formacie JSON:
            {{
                "keywords_analyzed": {keywords},
                "mentions": [
                    {{
                        "keyword": "słowo",
                        "mention": "treść wzmianki",
                        "source": "źródło",
                        "sentiment": "positive/negative/neutral",
                        "reach": "high/medium/low",
                        "date": "data (jeśli dostępna)",
                        "url": "link (jeśli dostępny)"
                    }}
                ],
                "summary": {{
                    "total_mentions": liczba,
                    "positive": liczba,
                    "negative": liczba,
                    "neutral": liczba
                }},
                "notable_mentions": ["najważniejsze wzmianki"]
            }}
            """,
            agent=monitor,
            expected_output="Keyword mentions in JSON format",
        )

        crew = Crew(
            agents=[monitor],
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

                # Create alerts for negative mentions
                if alert_on_mention:
                    for mention in parsed.get("mentions", []):
                        if mention.get("sentiment") == "negative" and mention.get("reach") in ["high", "medium"]:
                            await self.alert_service.create_alert(
                                company_id=company_id,
                                alert_type=AlertType.TREND_COMPETITOR_ACTION,
                                priority=AlertPriority.HIGH if mention.get("reach") == "high" else AlertPriority.MEDIUM,
                                title=f"Negatywna wzmianka: {mention.get('keyword', '')}",
                                message=mention.get("mention", "")[:200],
                                data=mention,
                                suggested_actions=["Przeanalizuj kontekst", "Rozważ odpowiedź"],
                                source_monitor="trend_monitor",
                            )

                return {"success": True, "monitoring": parsed}

            except json.JSONDecodeError:
                pass

        return {"success": True, "monitoring": {"raw_content": result_text}}

"""Proactive Suggestions Service - inteligentne sugestie dla firm.

Analizuje trendy i kalendarz aby proaktywnie sugerować:
- Treści do publikacji
- Kampanie marketingowe
- Okazje biznesowe
"""

from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings
from app.services.agents.tools.web_search import TavilySearchTool, TavilyTrendsTool


# Polish holidays and special days for marketing
POLISH_CALENDAR_EVENTS = [
    # Stałe święta
    {"date": "01-01", "name": "Nowy Rok", "type": "holiday", "marketing_tip": "Posty o postanowieniach, nowe początki"},
    {"date": "01-06", "name": "Trzech Króli", "type": "holiday", "marketing_tip": "Ostatni dzień świąteczny, wyprzedaże poświąteczne"},
    {"date": "02-14", "name": "Walentynki", "type": "commercial", "marketing_tip": "Promocje dla par, prezenty, romantyczne treści"},
    {"date": "03-08", "name": "Dzień Kobiet", "type": "commercial", "marketing_tip": "Promocje dla kobiet, kwiaty, prezenty"},
    {"date": "03-21", "name": "Pierwszy dzień wiosny", "type": "seasonal", "marketing_tip": "Wiosenne kolekcje, odnowa, świeżość"},
    {"date": "05-01", "name": "Święto Pracy", "type": "holiday", "marketing_tip": "Długi weekend, podróże, odpoczynek"},
    {"date": "05-03", "name": "Święto Konstytucji", "type": "holiday", "marketing_tip": "Patriotyczne treści, polski design"},
    {"date": "05-26", "name": "Dzień Matki", "type": "commercial", "marketing_tip": "Prezenty dla mam, emocjonalne treści"},
    {"date": "06-01", "name": "Dzień Dziecka", "type": "commercial", "marketing_tip": "Produkty dla dzieci, rodzinne treści"},
    {"date": "06-23", "name": "Dzień Ojca", "type": "commercial", "marketing_tip": "Prezenty dla ojców"},
    {"date": "06-21", "name": "Pierwszy dzień lata", "type": "seasonal", "marketing_tip": "Letnie kolekcje, wakacje, outdoor"},
    {"date": "08-15", "name": "Wniebowzięcie NMP", "type": "holiday", "marketing_tip": "Długi weekend, last minute wakacje"},
    {"date": "09-01", "name": "Back to School", "type": "commercial", "marketing_tip": "Produkty szkolne, nowy początek"},
    {"date": "09-23", "name": "Pierwszy dzień jesieni", "type": "seasonal", "marketing_tip": "Jesienne kolekcje, przytulność"},
    {"date": "10-31", "name": "Halloween", "type": "commercial", "marketing_tip": "Straszne promocje, tematyczne treści"},
    {"date": "11-01", "name": "Wszystkich Świętych", "type": "holiday", "marketing_tip": "Ostrożnie z marketingiem, refleksyjne treści"},
    {"date": "11-11", "name": "Święto Niepodległości", "type": "holiday", "marketing_tip": "Patriotyczne treści"},
    {"date": "11-29", "name": "Black Friday", "type": "commercial", "marketing_tip": "Wielkie promocje, pilność zakupów"},
    {"date": "12-02", "name": "Cyber Monday", "type": "commercial", "marketing_tip": "Promocje online"},
    {"date": "12-06", "name": "Mikołajki", "type": "commercial", "marketing_tip": "Prezenty, świąteczny nastrój"},
    {"date": "12-21", "name": "Pierwszy dzień zimy", "type": "seasonal", "marketing_tip": "Zimowe kolekcje, ciepło"},
    {"date": "12-24", "name": "Wigilia", "type": "holiday", "marketing_tip": "Życzenia świąteczne, rodzina"},
    {"date": "12-25", "name": "Boże Narodzenie", "type": "holiday", "marketing_tip": "Życzenia, rodzinne treści"},
    {"date": "12-26", "name": "Drugi dzień świąt", "type": "holiday", "marketing_tip": "Wyprzedaże poświąteczne"},
    {"date": "12-31", "name": "Sylwester", "type": "commercial", "marketing_tip": "Imprezy, podsumowania roku"},
]


class SuggestionType:
    """Types of proactive suggestions."""
    CALENDAR_EVENT = "calendar_event"  # Nadchodzące wydarzenie z kalendarza
    TREND_OPPORTUNITY = "trend_opportunity"  # Okazja związana z trendem
    CONTENT_IDEA = "content_idea"  # Pomysł na content
    CAMPAIGN_REMINDER = "campaign_reminder"  # Przypomnienie o kampanii


class ProactiveSuggestionsService:
    """Service for generating proactive suggestions for companies."""

    def __init__(self):
        self.search_tool = None
        self.trends_tool = None

    def _ensure_tools(self):
        """Lazy initialization of tools."""
        if self.search_tool is None:
            self.search_tool = TavilySearchTool()
        if self.trends_tool is None:
            self.trends_tool = TavilyTrendsTool()

    def get_upcoming_events(self, days_ahead: int = 14) -> list[dict[str, Any]]:
        """Get calendar events in the next N days."""
        today = datetime.now()
        upcoming = []

        for event in POLISH_CALENDAR_EVENTS:
            # Parse event date for this year
            month_day = event["date"]
            event_date = datetime.strptime(f"{today.year}-{month_day}", "%Y-%m-%d")

            # If event already passed this year, check next year
            if event_date < today:
                event_date = datetime.strptime(f"{today.year + 1}-{month_day}", "%Y-%m-%d")

            # Check if within range
            days_until = (event_date - today).days
            if 0 <= days_until <= days_ahead:
                upcoming.append({
                    **event,
                    "date_full": event_date.strftime("%Y-%m-%d"),
                    "days_until": days_until,
                    "suggestion_type": SuggestionType.CALENDAR_EVENT,
                })

        return sorted(upcoming, key=lambda x: x["days_until"])

    async def get_trend_suggestions(
        self,
        industry: str,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Get suggestions based on current trends in the industry."""
        self._ensure_tools()

        try:
            # Use Tavily to find trends
            trends_result = self.trends_tool._run(industry)

            suggestions = []
            if trends_result and "Blad" not in trends_result:
                suggestions.append({
                    "suggestion_type": SuggestionType.TREND_OPPORTUNITY,
                    "title": f"Trendy w branży: {industry}",
                    "content": trends_result[:500],
                    "action": "Rozważ content związany z aktualnymi trendami",
                    "priority": "medium",
                })

            return suggestions[:limit]

        except Exception:
            return []

    def generate_content_ideas(
        self,
        upcoming_events: list[dict],
        brand_voice: str = "profesjonalny",
        industry: str = "",
    ) -> list[dict[str, Any]]:
        """Generate content ideas based on upcoming events and brand."""
        ideas = []

        for event in upcoming_events[:5]:  # Top 5 events
            days = event["days_until"]

            # Determine urgency
            if days <= 3:
                priority = "high"
                urgency = "PILNE"
            elif days <= 7:
                priority = "medium"
                urgency = "Wkrótce"
            else:
                priority = "low"
                urgency = "Zaplanuj"

            idea = {
                "suggestion_type": SuggestionType.CONTENT_IDEA,
                "title": f"{urgency}: {event['name']} za {days} dni",
                "event_name": event["name"],
                "event_date": event["date_full"],
                "days_until": days,
                "marketing_tip": event["marketing_tip"],
                "priority": priority,
                "suggested_actions": [
                    f"Przygotuj post na Instagram",
                    f"Stwórz grafikę tematyczną",
                    f"Zaplanuj promocję/kampanię",
                ],
            }

            # Add industry-specific suggestions if available
            if industry:
                idea["industry_angle"] = f"Dopasuj treść do branży: {industry}"

            ideas.append(idea)

        return ideas

    async def get_all_suggestions(
        self,
        company_id: str,
        industry: str = "",
        brand_voice: str = "profesjonalny",
        days_ahead: int = 14,
    ) -> dict[str, Any]:
        """Get all proactive suggestions for a company.

        Returns:
            Dictionary with categorized suggestions
        """
        # Get upcoming calendar events
        upcoming_events = self.get_upcoming_events(days_ahead)

        # Generate content ideas from events
        content_ideas = self.generate_content_ideas(
            upcoming_events=upcoming_events,
            brand_voice=brand_voice,
            industry=industry,
        )

        # Get trend-based suggestions
        trend_suggestions = []
        if industry:
            trend_suggestions = await self.get_trend_suggestions(industry)

        # Categorize by priority
        high_priority = [s for s in content_ideas if s.get("priority") == "high"]
        medium_priority = [s for s in content_ideas if s.get("priority") == "medium"]
        low_priority = [s for s in content_ideas if s.get("priority") == "low"]

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "company_id": company_id,
            "summary": {
                "total_suggestions": len(content_ideas) + len(trend_suggestions),
                "high_priority": len(high_priority),
                "upcoming_events": len(upcoming_events),
            },
            "urgent": high_priority,
            "upcoming": medium_priority,
            "planned": low_priority,
            "trends": trend_suggestions,
            "calendar_events": upcoming_events,
        }


# Singleton instance
suggestions_service = ProactiveSuggestionsService()


async def get_suggestions_service() -> ProactiveSuggestionsService:
    """Get the suggestions service instance."""
    return suggestions_service

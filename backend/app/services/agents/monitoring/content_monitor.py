"""Content Monitor - Proactive content calendar alerts."""

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
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY,
    )


class ContentMonitor:
    """Monitor for content-related alerts."""

    def __init__(self, db):
        """Initialize with database."""
        self.db = db
        self.alert_service = AlertService(db)

    async def check_content_calendar(
        self,
        company_id: str,
        scheduled_posts: list[dict],
        days_to_check: int = 7,
        min_posts_per_week: int = 3,
    ) -> list[dict]:
        """Check content calendar and generate alerts.

        Args:
            company_id: Company ID
            scheduled_posts: List of scheduled posts
                [{"id": "...", "platform": "...", "scheduled_at": datetime, "status": "..."}]
            days_to_check: Days ahead to check
            min_posts_per_week: Minimum posts expected per week

        Returns:
            List of generated alerts
        """
        generated_alerts = []
        today = datetime.utcnow()
        week_end = today + timedelta(days=days_to_check)

        # Filter upcoming posts
        upcoming_posts = [
            p for p in scheduled_posts
            if p.get("status") != "published"
            and today <= self._parse_date(p.get("scheduled_at", today)) <= week_end
        ]

        post_count = len(upcoming_posts)

        # Check if calendar is empty or low
        if post_count == 0:
            alert = await self.alert_service.create_alert(
                company_id=company_id,
                alert_type=AlertType.CONTENT_CALENDAR_EMPTY,
                priority=AlertPriority.HIGH,
                title="Pusty kalendarz treści",
                message=f"Nie masz zaplanowanych żadnych postów na najbliższe "
                        f"{days_to_check} dni. Twoja obecność w social media może ucierpieć.",
                data={
                    "days_checked": days_to_check,
                    "posts_scheduled": 0,
                    "recommended_posts": min_posts_per_week,
                },
                action_url="/dashboard/marketing/calendar",
                action_label="Zaplanuj posty",
                suggested_actions=[
                    "Użyj agenta Instagram Specialist do stworzenia postów",
                    "Sprawdź sugestie trendów i wydarzeń",
                    "Przygotuj content na nadchodzące święta",
                ],
                source_monitor="content_monitor",
            )
            generated_alerts.append(alert.model_dump())

        elif post_count < min_posts_per_week:
            alert = await self.alert_service.create_alert(
                company_id=company_id,
                alert_type=AlertType.CONTENT_CALENDAR_EMPTY,
                priority=AlertPriority.MEDIUM,
                title="Mało zaplanowanych postów",
                message=f"Masz tylko {post_count} postów na najbliższe {days_to_check} dni. "
                        f"Zalecane minimum to {min_posts_per_week}.",
                data={
                    "days_checked": days_to_check,
                    "posts_scheduled": post_count,
                    "recommended_posts": min_posts_per_week,
                },
                action_url="/dashboard/marketing/calendar",
                action_label="Dodaj więcej postów",
                suggested_actions=[
                    "Przygotuj dodatkowe posty na wolne dni",
                    "Sprawdź jakie treści działały najlepiej",
                ],
                source_monitor="content_monitor",
            )
            generated_alerts.append(alert.model_dump())

        return generated_alerts

    async def check_content_performance(
        self,
        company_id: str,
        recent_posts: list[dict],
        engagement_threshold: float = 2.0,
    ) -> list[dict]:
        """Check recent content performance.

        Args:
            company_id: Company ID
            recent_posts: Recent posts with metrics
                [{"id": "...", "content": "...", "likes": X, "comments": Y, "impressions": Z}]
            engagement_threshold: Minimum engagement rate (%)

        Returns:
            List of generated alerts
        """
        generated_alerts = []

        if not recent_posts:
            return generated_alerts

        # Calculate engagement rates
        high_performers = []
        low_performers = []

        for post in recent_posts:
            impressions = post.get("impressions", 0)
            if impressions == 0:
                continue

            engagements = post.get("likes", 0) + post.get("comments", 0) + post.get("shares", 0)
            engagement_rate = (engagements / impressions) * 100

            post["engagement_rate"] = round(engagement_rate, 2)

            if engagement_rate >= engagement_threshold * 2:
                high_performers.append(post)
            elif engagement_rate < engagement_threshold / 2:
                low_performers.append(post)

        # Alert for viral content
        if high_performers:
            best = max(high_performers, key=lambda p: p["engagement_rate"])
            alert = await self.alert_service.create_alert(
                company_id=company_id,
                alert_type=AlertType.CONTENT_VIRAL_POST,
                priority=AlertPriority.LOW,
                title="Post z wysokim engagement!",
                message=f"Twój post osiągnął {best['engagement_rate']}% engagement rate! "
                        f"To doskonały wynik - rozważ podobne treści w przyszłości.",
                data={
                    "post_id": best.get("id"),
                    "engagement_rate": best["engagement_rate"],
                    "likes": best.get("likes", 0),
                    "comments": best.get("comments", 0),
                },
                action_url=f"/dashboard/marketing/posts/{best.get('id')}",
                action_label="Zobacz post",
                suggested_actions=[
                    "Przeanalizuj co zadziałało w tym poście",
                    "Stwórz podobne treści",
                    "Rozważ promocję tego posta",
                ],
                source_monitor="content_monitor",
                source_entity_id=best.get("id"),
            )
            generated_alerts.append(alert.model_dump())

        # Alert for low engagement
        if len(low_performers) >= 3:
            avg_engagement = sum(p["engagement_rate"] for p in low_performers) / len(low_performers)
            alert = await self.alert_service.create_alert(
                company_id=company_id,
                alert_type=AlertType.CONTENT_LOW_ENGAGEMENT,
                priority=AlertPriority.MEDIUM,
                title="Niski engagement ostatnich postów",
                message=f"Ostatnie {len(low_performers)} postów ma średni engagement "
                        f"tylko {avg_engagement:.1f}%. Rozważ zmianę strategii content.",
                data={
                    "low_performing_count": len(low_performers),
                    "average_engagement": round(avg_engagement, 2),
                    "threshold": engagement_threshold,
                },
                action_url="/dashboard/marketing/analytics",
                action_label="Zobacz analitykę",
                suggested_actions=[
                    "Przeanalizuj godziny publikacji",
                    "Sprawdź czy treści są dopasowane do odbiorców",
                    "Eksperymentuj z różnymi formatami",
                    "Przeprowadź test A/B",
                ],
                source_monitor="content_monitor",
            )
            generated_alerts.append(alert.model_dump())

        return generated_alerts

    async def suggest_content_ideas(
        self,
        company_id: str,
        industry: str,
        recent_topics: list[str] | None = None,
        upcoming_events: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Generate content ideas based on context.

        Args:
            company_id: Company ID
            industry: Company industry
            recent_topics: Topics recently covered
            upcoming_events: Upcoming events/holidays

        Returns:
            Dictionary with content suggestions
        """
        llm = _get_llm()

        content_strategist = Agent(
            role="Content Strategist",
            goal="Generować kreatywne pomysły na content dopasowane do branży",
            backstory="""Jesteś strategiem content marketingu z wieloletnim
            doświadczeniem w polskich social media. Wiesz co działa na
            Instagramie, Facebooku i LinkedIn.""",
            tools=[],
            llm=llm,
            verbose=False,
        )

        recent_text = ", ".join(recent_topics or ["brak danych"])
        events_text = ""
        if upcoming_events:
            for e in upcoming_events[:5]:
                events_text += f"- {e.get('date', '?')}: {e.get('name', '?')}\n"

        task = Task(
            description=f"""
            Zaproponuj pomysły na content dla firmy z branży: {industry}

            OSTATNIO PORUSZANE TEMATY (unikaj powtórek):
            {recent_text}

            NADCHODZĄCE WYDARZENIA/ŚWIĘTA:
            {events_text or "Brak specjalnych wydarzeń"}

            PRZYGOTUJ:
            1. 5 pomysłów na posty na Instagram
            2. 3 pomysły na dłuższe formy (carousel, reel)
            3. 2 pomysły związane z wydarzeniami

            Zwróć w formacie JSON:
            {{
                "quick_posts": [
                    {{
                        "idea": "pomysł",
                        "hook": "pierwsze zdanie przykuwające uwagę",
                        "hashtags": ["tagi"],
                        "best_time": "najlepsza pora publikacji"
                    }}
                ],
                "long_form": [
                    {{
                        "type": "carousel/reel/story series",
                        "idea": "pomysł",
                        "outline": ["punkt 1", "punkt 2"]
                    }}
                ],
                "event_based": [
                    {{
                        "event": "wydarzenie",
                        "idea": "pomysł na post",
                        "angle": "kąt/podejście"
                    }}
                ],
                "content_calendar_suggestion": {{
                    "monday": "typ contentu",
                    "wednesday": "typ contentu",
                    "friday": "typ contentu"
                }}
            }}
            """,
            agent=content_strategist,
            expected_output="Content ideas in JSON format",
        )

        crew = Crew(
            agents=[content_strategist],
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
                return {"success": True, "ideas": parsed}
            except json.JSONDecodeError:
                pass

        return {"success": True, "ideas": {"raw_content": result_text}}

    def _parse_date(self, date_value) -> datetime:
        """Parse date from various formats."""
        if isinstance(date_value, datetime):
            return date_value
        if isinstance(date_value, str):
            return datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        return datetime.utcnow()

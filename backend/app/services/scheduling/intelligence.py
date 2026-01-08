"""Scheduling intelligence service for optimal publication time suggestions."""

from datetime import datetime, timedelta
from typing import Any

from app.models.scheduled_content import ContentPlatform, ContentType, ScheduledContent


class ScheduleSuggestion:
    """A single scheduling suggestion."""

    def __init__(
        self,
        time: datetime,
        score: float,
        reasoning: str,
        is_primary: bool = False,
    ):
        self.time = time
        self.score = score
        self.reasoning = reasoning
        self.is_primary = is_primary

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time.isoformat(),
            "score": round(self.score, 2),
            "reasoning": self.reasoning,
            "is_primary": self.is_primary,
        }


class SchedulingIntelligence:
    """Service for suggesting optimal publication times."""

    # Default optimal times per platform (based on general best practices)
    DEFAULT_BEST_TIMES: dict[str, dict[str, list[str]]] = {
        "instagram": {
            "weekday": ["08:00", "12:00", "18:00", "21:00"],
            "weekend": ["10:00", "14:00", "20:00"],
        },
        "facebook": {
            "weekday": ["09:00", "13:00", "16:00", "19:00"],
            "weekend": ["12:00", "15:00", "18:00"],
        },
        "linkedin": {
            "weekday": ["07:30", "12:00", "17:30"],
            "weekend": [],  # LinkedIn is weak on weekends
        },
        "twitter": {
            "weekday": ["08:00", "12:00", "17:00", "21:00"],
            "weekend": ["09:00", "12:00", "18:00"],
        },
        "email": {
            "weekday": ["09:00", "14:00"],
            "weekend": [],  # Email newsletters typically avoid weekends
        },
    }

    # Platform-specific reasoning templates
    REASONING_TEMPLATES = {
        "instagram": {
            "morning": "Poranna aktywność na Instagramie jest wysoka - użytkownicy sprawdzają feed przed pracą.",
            "noon": "Przerwa lunchowa to jeden z najaktywniejszych momentów na Instagramie.",
            "evening": "Wieczorem użytkownicy relaksują się przeglądając Instagram.",
            "weekend": "Weekendowe poranki to dobry czas na Instagram - ludzie mają więcej wolnego czasu.",
        },
        "facebook": {
            "morning": "Rano użytkownicy Facebooka sprawdzają wiadomości i aktualności.",
            "noon": "Przerwa lunchowa generuje duży ruch na Facebooku.",
            "evening": "Popołudniowe godziny to czas relaksu i przeglądania Facebooka.",
            "weekend": "Weekendy przynoszą zwiększoną aktywność na Facebooku.",
        },
        "linkedin": {
            "morning": "Poranna kawa + LinkedIn to nawyk profesjonalistów.",
            "noon": "Przerwa lunchowa to popularny czas na sprawdzenie LinkedIn.",
            "evening": "Koniec dnia pracy - idealna pora na treści biznesowe.",
            "weekend": "LinkedIn ma niską aktywność w weekendy - zalecamy dni robocze.",
        },
        "twitter": {
            "morning": "Poranne godziny to czas nadrabiania newsów na X/Twitter.",
            "noon": "Przerwa lunchowa generuje spike w aktywności na X/Twitter.",
            "evening": "Wieczorna aktywność na X/Twitter jest stabilnie wysoka.",
            "weekend": "Weekendowy Twitter ma inną dynamikę - więcej lifestyle content.",
        },
        "email": {
            "morning": "Poranek w dni robocze to optymalny czas na newslettery.",
            "noon": "Wczesne popołudnie - drugi szczyt otwieralności maili.",
            "evening": "Wieczorne maile mają niższą otwieralność.",
            "weekend": "Weekendowe newslettery mają znacznie niższą otwieralność.",
        },
    }

    def __init__(self):
        pass

    async def suggest_time(
        self,
        company_id: str,
        content_type: ContentType,
        platform: ContentPlatform,
        content: dict[str, Any] | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Suggest optimal publication time.

        Args:
            company_id: Company ID for personalization
            content_type: Type of content
            platform: Target platform
            content: Content data (for urgency analysis)
            preferences: User preferences (earliest, latest, avoid_weekends)

        Returns:
            Dictionary with primary suggestion and alternatives
        """
        preferences = preferences or {}

        # Parse date range preferences
        earliest = self._parse_date(preferences.get("earliest")) or datetime.utcnow()
        latest = self._parse_date(preferences.get("latest")) or (earliest + timedelta(days=7))
        avoid_weekends = preferences.get("avoid_weekends", False)

        # Get scheduled content to avoid collisions
        scheduled = await self._get_scheduled_content(company_id, earliest, latest)
        scheduled_times = {s.scheduled_for for s in scheduled if s.scheduled_for}

        # Get publication history for personalization (future enhancement)
        # history = await self._get_publication_history(company_id, platform)

        # Analyze content urgency
        urgency = self._analyze_content_urgency(content)

        # Calculate best slots
        suggestions = self._calculate_best_slots(
            platform=platform,
            earliest=earliest,
            latest=latest,
            avoid_weekends=avoid_weekends,
            scheduled_times=scheduled_times,
            urgency=urgency,
        )

        if not suggestions:
            # Fallback: next available slot
            fallback_time = earliest + timedelta(hours=2)
            suggestions = [
                ScheduleSuggestion(
                    time=fallback_time,
                    score=0.5,
                    reasoning="Brak optymalnych slotów - zaproponowano najbliższy dostępny termin.",
                    is_primary=True,
                )
            ]

        primary = next((s for s in suggestions if s.is_primary), suggestions[0])
        alternatives = [s for s in suggestions if not s.is_primary][:3]

        return {
            "suggested_time": primary.time.isoformat(),
            "confidence": primary.score,
            "reasoning": primary.reasoning,
            "alternatives": [alt.to_dict() for alt in alternatives],
        }

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            if "T" in date_str:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

    async def _get_scheduled_content(
        self,
        company_id: str,
        start: datetime,
        end: datetime,
    ) -> list[ScheduledContent]:
        """Get scheduled content in date range to avoid collisions."""
        from app.core.database import get_database

        db = get_database()
        cursor = db.scheduled_content.find({
            "company_id": company_id,
            "status": {"$in": ["scheduled", "queued", "pending_approval"]},
            "scheduled_for": {"$gte": start, "$lte": end},
        })

        results = []
        async for doc in cursor:
            results.append(ScheduledContent(**doc))
        return results

    def _analyze_content_urgency(self, content: dict[str, Any] | None) -> str:
        """
        Analyze content to determine urgency level.

        Returns: 'urgent', 'normal', or 'evergreen'
        """
        if not content:
            return "normal"

        text = str(content.get("text", "")).lower()

        # Keywords indicating urgency
        urgent_keywords = [
            "promocja", "rabat", "wyprzedaż", "ostatnie", "tylko dziś",
            "flash sale", "limitowana", "kończy się", "ostatnia szansa",
            "hot deal", "przecena", "okazja"
        ]

        # Keywords indicating evergreen content
        evergreen_keywords = [
            "porada", "tip", "jak", "dlaczego", "przewodnik", "tutorial",
            "wprowadzenie", "podstawy", "historia", "inspiracja"
        ]

        for keyword in urgent_keywords:
            if keyword in text:
                return "urgent"

        for keyword in evergreen_keywords:
            if keyword in text:
                return "evergreen"

        return "normal"

    def _calculate_best_slots(
        self,
        platform: ContentPlatform,
        earliest: datetime,
        latest: datetime,
        avoid_weekends: bool,
        scheduled_times: set[datetime],
        urgency: str,
    ) -> list[ScheduleSuggestion]:
        """Calculate best publication slots."""
        platform_key = platform.value
        platform_times = self.DEFAULT_BEST_TIMES.get(platform_key, {})
        reasoning_templates = self.REASONING_TEMPLATES.get(platform_key, {})

        suggestions = []
        current_date = earliest.date()
        end_date = latest.date()

        while current_date <= end_date:
            is_weekend = current_date.weekday() >= 5

            # Skip weekends if requested
            if avoid_weekends and is_weekend:
                current_date += timedelta(days=1)
                continue

            # Get times for this day type
            time_key = "weekend" if is_weekend else "weekday"
            day_times = platform_times.get(time_key, [])

            # For LinkedIn on weekends, skip
            if platform_key == "linkedin" and is_weekend:
                current_date += timedelta(days=1)
                continue

            for time_str in day_times:
                try:
                    hour, minute = map(int, time_str.split(":"))
                    slot_time = datetime(
                        current_date.year,
                        current_date.month,
                        current_date.day,
                        hour,
                        minute,
                    )

                    # Skip if in the past
                    if slot_time < datetime.utcnow():
                        continue

                    # Skip if outside range
                    if slot_time < earliest or slot_time > latest:
                        continue

                    # Check for collisions (within 2 hours)
                    has_collision = any(
                        abs((slot_time - st).total_seconds()) < 7200
                        for st in scheduled_times
                        if st
                    )
                    if has_collision:
                        continue

                    # Calculate score
                    score = self._calculate_slot_score(
                        slot_time=slot_time,
                        platform=platform_key,
                        urgency=urgency,
                        is_weekend=is_weekend,
                    )

                    # Get reasoning
                    reasoning = self._get_reasoning(
                        slot_time=slot_time,
                        platform_key=platform_key,
                        reasoning_templates=reasoning_templates,
                        is_weekend=is_weekend,
                    )

                    suggestions.append(
                        ScheduleSuggestion(
                            time=slot_time,
                            score=score,
                            reasoning=reasoning,
                        )
                    )
                except (ValueError, TypeError):
                    continue

            current_date += timedelta(days=1)

        # Sort by score and mark primary
        suggestions.sort(key=lambda s: s.score, reverse=True)

        # Adjust for urgency
        if urgency == "urgent" and suggestions:
            # For urgent content, prefer earlier slots
            suggestions.sort(key=lambda s: (s.time, -s.score))

        if suggestions:
            suggestions[0].is_primary = True

        return suggestions[:5]  # Return top 5

    def _calculate_slot_score(
        self,
        slot_time: datetime,
        platform: str,
        urgency: str,
        is_weekend: bool,
    ) -> float:
        """Calculate score for a time slot (0.0 - 1.0)."""
        base_score = 0.7

        hour = slot_time.hour

        # Peak hours bonus
        peak_hours = {
            "instagram": [8, 12, 18, 21],
            "facebook": [9, 13, 16, 19],
            "linkedin": [7, 12, 17],
            "twitter": [8, 12, 17, 21],
            "email": [9, 14],
        }

        if hour in peak_hours.get(platform, []):
            base_score += 0.2

        # Weekend penalty for business platforms
        if is_weekend and platform in ["linkedin", "email"]:
            base_score -= 0.3

        # Day of week preferences
        weekday = slot_time.weekday()
        if platform == "linkedin" and weekday in [1, 2, 3]:  # Tue, Wed, Thu
            base_score += 0.1
        elif platform == "instagram" and weekday in [3, 4]:  # Thu, Fri
            base_score += 0.05

        # Time freshness bonus (closer = slightly better for urgent)
        if urgency == "urgent":
            hours_from_now = (slot_time - datetime.utcnow()).total_seconds() / 3600
            if hours_from_now < 24:
                base_score += 0.1
            elif hours_from_now < 48:
                base_score += 0.05

        return min(max(base_score, 0.0), 1.0)

    def _get_reasoning(
        self,
        slot_time: datetime,
        platform_key: str,
        reasoning_templates: dict[str, str],
        is_weekend: bool,
    ) -> str:
        """Generate human-readable reasoning for the suggestion."""
        hour = slot_time.hour
        day_name = self._get_polish_day_name(slot_time.weekday())
        time_str = slot_time.strftime("%H:%M")

        if is_weekend:
            template = reasoning_templates.get(
                "weekend",
                f"Weekendowy termin na {platform_key}."
            )
        elif hour < 10:
            template = reasoning_templates.get(
                "morning",
                "Poranne godziny mają dobrą aktywność."
            )
        elif hour < 14:
            template = reasoning_templates.get(
                "noon",
                "Pora lunchu to aktywny czas w social media."
            )
        else:
            template = reasoning_templates.get(
                "evening",
                "Popołudniowe i wieczorne godziny generują wysoki engagement."
            )

        return f"{day_name} o {time_str} - {template}"

    def _get_polish_day_name(self, weekday: int) -> str:
        """Get Polish day name."""
        days = [
            "Poniedziałek",
            "Wtorek",
            "Środa",
            "Czwartek",
            "Piątek",
            "Sobota",
            "Niedziela",
        ]
        return days[weekday]

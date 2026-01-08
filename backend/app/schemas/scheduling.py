"""Schemas for scheduling suggestions."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.scheduled_content import ContentPlatform, ContentType


class SchedulePreferences(BaseModel):
    """User preferences for scheduling."""

    earliest: str | None = Field(
        None,
        description="Earliest date to consider (ISO format or YYYY-MM-DD)",
        examples=["2025-01-15", "2025-01-15T09:00:00"],
    )
    latest: str | None = Field(
        None,
        description="Latest date to consider (ISO format or YYYY-MM-DD)",
        examples=["2025-01-20", "2025-01-20T18:00:00"],
    )
    avoid_weekends: bool = Field(
        False,
        description="Whether to avoid suggesting weekend slots",
    )


class SuggestTimeRequest(BaseModel):
    """Request for scheduling suggestion."""

    content_type: ContentType = Field(
        ...,
        description="Type of content to schedule",
    )
    platform: ContentPlatform = Field(
        ...,
        description="Target platform for publication",
    )
    content: dict | None = Field(
        None,
        description="Content data for urgency analysis",
    )
    preferences: SchedulePreferences | None = Field(
        None,
        description="User preferences for scheduling",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content_type": "instagram_post",
                    "platform": "instagram",
                    "content": {
                        "text": "Nasza nowa kolekcja już dostępna! 🌸",
                        "hashtags": ["#nowość", "#kolekcja"],
                    },
                    "preferences": {
                        "earliest": "2025-01-15",
                        "latest": "2025-01-22",
                        "avoid_weekends": False,
                    },
                }
            ]
        }
    }


class TimeAlternative(BaseModel):
    """Alternative time suggestion."""

    time: datetime = Field(
        ...,
        description="Suggested publication time",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 - 1.0)",
    )
    reasoning: str = Field(
        ...,
        description="Explanation for this suggestion",
    )


class SuggestTimeResponse(BaseModel):
    """Response with scheduling suggestion."""

    suggested_time: datetime = Field(
        ...,
        description="Primary suggested publication time",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for primary suggestion (0.0 - 1.0)",
    )
    reasoning: str = Field(
        ...,
        description="Explanation for the primary suggestion",
    )
    alternatives: list[TimeAlternative] = Field(
        default_factory=list,
        description="Alternative time suggestions",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "suggested_time": "2025-01-16T18:00:00",
                    "confidence": 0.85,
                    "reasoning": "Środa o 18:00 - Wieczorem użytkownicy relaksują się przeglądając Instagram.",
                    "alternatives": [
                        {
                            "time": "2025-01-17T12:00:00",
                            "score": 0.78,
                            "reasoning": "Czwartek o 12:00 - Przerwa lunchowa to jeden z najaktywniejszych momentów na Instagramie.",
                        },
                        {
                            "time": "2025-01-15T21:00:00",
                            "score": 0.72,
                            "reasoning": "Środa o 21:00 - Wieczorna aktywność na Instagramie jest wysoka.",
                        },
                    ],
                }
            ]
        }
    }

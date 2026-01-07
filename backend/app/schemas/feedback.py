"""Feedback schemas for task rating and improvement tracking."""

from datetime import datetime
from pydantic import BaseModel, Field


class TaskFeedbackInput(BaseModel):
    """Input for submitting feedback on a task output."""

    rating: int = Field(..., ge=1, le=5, description="Ocena od 1 do 5")
    used: bool = Field(..., description="Czy output zostal uzyty")
    edited: bool = Field(default=False, description="Czy output wymagal edycji")
    edit_percentage: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Procent zmian wprowadzonych (0-100)"
    )
    comments: str | None = Field(default=None, max_length=1000, description="Dodatkowe uwagi")


class TaskFeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    id: str
    task_id: str
    rating: int
    used: bool
    edited: bool
    edit_percentage: int | None
    comments: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackStatsResponse(BaseModel):
    """Aggregated feedback statistics."""

    total_feedbacks: int
    average_rating: float
    usage_rate: float  # Procent outputow ktore zostaly uzyte
    edit_rate: float  # Procent outputow ktore wymagaly edycji
    average_edit_percentage: float | None
    rating_distribution: dict[str, int]  # {"1": 5, "2": 10, ...}


class AgentFeedbackStats(BaseModel):
    """Feedback statistics per agent."""

    agent: str
    department: str
    total_tasks: int
    total_feedbacks: int
    average_rating: float
    usage_rate: float
    satisfaction_score: float  # Kombinacja rating + usage - edit_rate

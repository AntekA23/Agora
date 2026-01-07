from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.task import TaskStatus


class InstagramTaskInput(BaseModel):
    """Input for Instagram post generation."""

    brief: str = Field(..., min_length=10, description="Brief opisujacy co ma zawierac post")
    post_type: str = Field(default="post", description="Typ: post, story, reel, carousel")
    include_hashtags: bool = Field(default=True, description="Czy dodac hashtagi")


class CopywriterTaskInput(BaseModel):
    """Input for copywriting task."""

    brief: str = Field(..., min_length=10)
    copy_type: str = Field(default="ad", description="Typ: ad, email, landing, slogan, description")
    max_length: int | None = Field(default=None, description="Max dlugosc w znakach")


class TaskCreate(BaseModel):
    """Create a new task."""

    department: str
    agent: str
    type: str
    input: dict[str, Any]


class TaskResponse(BaseModel):
    """Task response."""

    id: str
    company_id: str
    user_id: str
    department: str
    agent: str
    type: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    status: TaskStatus
    error: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """List of tasks response."""

    tasks: list[TaskResponse]
    total: int
    page: int
    per_page: int

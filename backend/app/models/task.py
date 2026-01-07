from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from app.models.base import MongoBaseModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(MongoBaseModel):
    """Task model for agent jobs."""

    company_id: str
    user_id: str
    department: str
    agent: str
    type: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] | None = None
    status: TaskStatus = TaskStatus.PENDING
    error: str | None = None
    completed_at: datetime | None = None

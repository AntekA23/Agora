"""Conversation model for chat sessions."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from app.models.base import MongoBaseModel


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    TEXT = "text"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    SUGGESTION = "suggestion"
    ACTION = "action"


class ConversationMessage(MongoBaseModel):
    """Individual message in a conversation."""

    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    metadata: dict[str, Any] = Field(default_factory=dict)
    # For task-related messages
    task_id: str | None = None
    task_status: str | None = None
    task_output: dict[str, Any] | None = None
    # For action buttons in messages
    actions: list[dict[str, str]] = Field(default_factory=list)


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Conversation(MongoBaseModel):
    """Conversation session model."""

    company_id: str
    user_id: str
    title: str = "Nowa rozmowa"
    status: ConversationStatus = ConversationStatus.ACTIVE
    messages: list[dict[str, Any]] = Field(default_factory=list)
    # Context for the conversation
    context: dict[str, Any] = Field(default_factory=dict)
    # Related tasks created during conversation
    task_ids: list[str] = Field(default_factory=list)
    # Last activity
    last_message_at: datetime | None = None

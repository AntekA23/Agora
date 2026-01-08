"""Schemas for schedule rules API."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.scheduled_content import ContentPlatform, ContentType
from app.models.schedule_rule import (
    ApprovalMode,
    ContentCategory,
    RuleFrequency,
)


# --- Nested schemas ---


class ScheduleConfigCreate(BaseModel):
    """Schema for creating schedule configuration."""

    frequency: RuleFrequency = RuleFrequency.WEEKLY
    days_of_week: list[int] = Field(
        default_factory=lambda: [0],
        description="Days of week (0=Monday, 6=Sunday)",
    )
    day_of_month: int | None = Field(
        None,
        ge=1,
        le=31,
        description="Day of month for monthly frequency",
    )
    time: str = Field(
        "08:00",
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Time to generate/publish (HH:MM format)",
    )
    timezone: str = Field(
        "Europe/Warsaw",
        description="Timezone for scheduling",
    )


class ContentTemplateCreate(BaseModel):
    """Schema for creating content template."""

    category: ContentCategory = ContentCategory.CUSTOM
    prompt_template: str = Field(
        "",
        max_length=2000,
        description="Custom prompt template",
    )
    style: str = Field(
        "profesjonalny",
        max_length=50,
        description="Style/tone of content",
    )
    include_hashtags: bool = True
    include_emoji: bool = True
    generate_image: bool = False
    additional_instructions: str = Field(
        "",
        max_length=500,
        description="Additional instructions for AI",
    )


# --- Request schemas ---


class ScheduleRuleCreate(BaseModel):
    """Schema for creating a schedule rule."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the rule",
    )
    description: str | None = Field(
        None,
        max_length=500,
    )
    content_type: ContentType = ContentType.INSTAGRAM_POST
    platform: ContentPlatform = ContentPlatform.INSTAGRAM
    content_template: ContentTemplateCreate = Field(
        default_factory=ContentTemplateCreate,
    )
    schedule: ScheduleConfigCreate = Field(
        default_factory=ScheduleConfigCreate,
    )
    approval_mode: ApprovalMode = ApprovalMode.REQUIRE_APPROVAL
    notify_before_publish: bool = True
    notification_minutes: int = Field(60, ge=5, le=1440)
    fallback_on_no_response: str = Field(
        "publish",
        pattern=r"^(publish|skip)$",
    )
    max_queue_size: int = Field(4, ge=1, le=20)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Motywacyjne poniedziałki",
                    "description": "Automatyczne posty motywacyjne na początek tygodnia",
                    "content_type": "instagram_post",
                    "platform": "instagram",
                    "content_template": {
                        "category": "motivational",
                        "style": "inspirujący",
                        "include_hashtags": True,
                        "include_emoji": True,
                        "additional_instructions": "Nawiązuj do początku tygodnia",
                    },
                    "schedule": {
                        "frequency": "weekly",
                        "days_of_week": [0],
                        "time": "08:00",
                        "timezone": "Europe/Warsaw",
                    },
                    "approval_mode": "require_approval",
                    "notification_minutes": 60,
                    "max_queue_size": 4,
                }
            ]
        }
    }


class ScheduleRuleUpdate(BaseModel):
    """Schema for updating a schedule rule."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    content_template: ContentTemplateCreate | None = None
    schedule: ScheduleConfigCreate | None = None
    approval_mode: ApprovalMode | None = None
    notify_before_publish: bool | None = None
    notification_minutes: int | None = Field(None, ge=5, le=1440)
    fallback_on_no_response: str | None = Field(None, pattern=r"^(publish|skip)$")
    max_queue_size: int | None = Field(None, ge=1, le=20)


# --- Response schemas ---


class ScheduleConfigResponse(BaseModel):
    """Response schema for schedule configuration."""

    frequency: RuleFrequency
    days_of_week: list[int]
    day_of_month: int | None
    time: str
    timezone: str


class ContentTemplateResponse(BaseModel):
    """Response schema for content template."""

    category: ContentCategory
    prompt_template: str
    style: str
    include_hashtags: bool
    include_emoji: bool
    generate_image: bool
    additional_instructions: str


class ScheduleRuleResponse(BaseModel):
    """Response schema for a schedule rule."""

    id: str
    company_id: str
    created_by: str
    name: str
    description: str | None
    content_type: ContentType
    platform: ContentPlatform
    content_template: ContentTemplateResponse
    schedule: ScheduleConfigResponse
    approval_mode: ApprovalMode
    notify_before_publish: bool
    notification_minutes: int
    fallback_on_no_response: str
    is_active: bool
    last_executed: datetime | None
    next_execution: datetime | None
    last_error: str | None
    max_queue_size: int
    total_generated: int
    total_published: int
    created_at: datetime
    updated_at: datetime

    # Computed fields
    queue_count: int = Field(
        0,
        description="Current number of items in queue from this rule",
    )


class ScheduleRuleListResponse(BaseModel):
    """Response schema for list of schedule rules."""

    items: list[ScheduleRuleResponse]
    total: int
    active_count: int
    paused_count: int


class ScheduleRuleStats(BaseModel):
    """Statistics for schedule rules."""

    total_rules: int
    active_rules: int
    paused_rules: int
    total_generated: int
    total_published: int
    next_executions: list[dict]  # [{rule_name, next_execution}]


# --- Action schemas ---


class GenerateNowRequest(BaseModel):
    """Request to force generation now."""

    schedule_for: datetime | None = Field(
        None,
        description="Optional: schedule the generated content for this time",
    )


class GenerateNowResponse(BaseModel):
    """Response from force generation."""

    success: bool
    scheduled_content_id: str | None = None
    error: str | None = None

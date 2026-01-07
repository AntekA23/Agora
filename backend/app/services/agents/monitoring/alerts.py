"""Alert System for Proactive Monitoring."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from bson import ObjectId


class AlertType(str, Enum):
    """Types of alerts."""
    CASHFLOW_LOW_BALANCE = "cashflow_low_balance"
    CASHFLOW_UNUSUAL_SPENDING = "cashflow_unusual_spending"
    CASHFLOW_POSITIVE_TREND = "cashflow_positive_trend"

    INVOICE_OVERDUE = "invoice_overdue"
    INVOICE_DUE_SOON = "invoice_due_soon"
    INVOICE_PAYMENT_RECEIVED = "invoice_payment_received"

    CONTENT_CALENDAR_EMPTY = "content_calendar_empty"
    CONTENT_LOW_ENGAGEMENT = "content_low_engagement"
    CONTENT_VIRAL_POST = "content_viral_post"

    TREND_NEW_INDUSTRY = "trend_new_industry"
    TREND_COMPETITOR_ACTION = "trend_competitor_action"
    TREND_OPPORTUNITY = "trend_opportunity"

    REVIEW_NEW_POSITIVE = "review_new_positive"
    REVIEW_NEW_NEGATIVE = "review_new_negative"
    REVIEW_RESPONSE_NEEDED = "review_response_needed"

    SYSTEM_INFO = "system_info"
    CUSTOM = "custom"


class AlertPriority(str, Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Alert(BaseModel):
    """Alert model."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    company_id: str
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)

    # Actions
    action_url: str | None = None
    action_label: str | None = None
    suggested_actions: list[str] = Field(default_factory=list)

    # Status
    read: bool = False
    dismissed: bool = False
    acted_upon: bool = False

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: datetime | None = None
    expires_at: datetime | None = None

    # Source
    source_monitor: str = ""
    source_entity_id: str | None = None


class AlertService:
    """Service for managing alerts."""

    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
        self.collection = db.alerts

    async def create_alert(
        self,
        company_id: str,
        alert_type: AlertType,
        priority: AlertPriority,
        title: str,
        message: str,
        data: dict | None = None,
        action_url: str | None = None,
        action_label: str | None = None,
        suggested_actions: list[str] | None = None,
        source_monitor: str = "",
        source_entity_id: str | None = None,
        expires_at: datetime | None = None,
    ) -> Alert:
        """Create a new alert."""
        alert = Alert(
            company_id=company_id,
            type=alert_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            action_url=action_url,
            action_label=action_label,
            suggested_actions=suggested_actions or [],
            source_monitor=source_monitor,
            source_entity_id=source_entity_id,
            expires_at=expires_at,
        )

        # Check for duplicate recent alerts
        existing = await self.collection.find_one({
            "company_id": company_id,
            "type": alert_type.value,
            "source_entity_id": source_entity_id,
            "dismissed": False,
            "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)},
        })

        if existing:
            # Don't create duplicate alerts for same entity on same day
            return Alert(**{**existing, "id": str(existing["_id"])})

        # Insert alert
        doc = alert.model_dump()
        doc["_id"] = ObjectId(alert.id)
        del doc["id"]

        await self.collection.insert_one(doc)

        return alert

    async def get_alerts(
        self,
        company_id: str,
        unread_only: bool = False,
        priority: AlertPriority | None = None,
        alert_type: AlertType | None = None,
        limit: int = 50,
    ) -> list[Alert]:
        """Get alerts for a company."""
        query: dict = {
            "company_id": company_id,
            "dismissed": False,
        }

        if unread_only:
            query["read"] = False

        if priority:
            query["priority"] = priority.value

        if alert_type:
            query["type"] = alert_type.value

        # Exclude expired alerts
        query["$or"] = [
            {"expires_at": None},
            {"expires_at": {"$gt": datetime.utcnow()}},
        ]

        alerts = []
        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)

        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
            alerts.append(Alert(**doc))

        return alerts

    async def get_unread_count(self, company_id: str) -> dict[str, int]:
        """Get count of unread alerts by priority."""
        pipeline = [
            {
                "$match": {
                    "company_id": company_id,
                    "read": False,
                    "dismissed": False,
                    "$or": [
                        {"expires_at": None},
                        {"expires_at": {"$gt": datetime.utcnow()}},
                    ],
                }
            },
            {
                "$group": {
                    "_id": "$priority",
                    "count": {"$sum": 1},
                }
            },
        ]

        counts = {"total": 0, "urgent": 0, "high": 0, "medium": 0, "low": 0}

        async for doc in self.collection.aggregate(pipeline):
            priority = doc["_id"]
            count = doc["count"]
            counts[priority] = count
            counts["total"] += count

        return counts

    async def mark_as_read(self, alert_id: str, company_id: str) -> bool:
        """Mark an alert as read."""
        result = await self.collection.update_one(
            {"_id": ObjectId(alert_id), "company_id": company_id},
            {"$set": {"read": True, "read_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def mark_all_as_read(self, company_id: str) -> int:
        """Mark all alerts as read for a company."""
        result = await self.collection.update_many(
            {"company_id": company_id, "read": False},
            {"$set": {"read": True, "read_at": datetime.utcnow()}},
        )
        return result.modified_count

    async def dismiss_alert(self, alert_id: str, company_id: str) -> bool:
        """Dismiss an alert."""
        result = await self.collection.update_one(
            {"_id": ObjectId(alert_id), "company_id": company_id},
            {"$set": {"dismissed": True}},
        )
        return result.modified_count > 0

    async def mark_acted_upon(self, alert_id: str, company_id: str) -> bool:
        """Mark an alert as acted upon."""
        result = await self.collection.update_one(
            {"_id": ObjectId(alert_id), "company_id": company_id},
            {"$set": {"acted_upon": True, "read": True}},
        )
        return result.modified_count > 0

    async def delete_old_alerts(self, days: int = 30) -> int:
        """Delete alerts older than specified days."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.collection.delete_many({
            "created_at": {"$lt": cutoff},
            "dismissed": True,
        })
        return result.deleted_count

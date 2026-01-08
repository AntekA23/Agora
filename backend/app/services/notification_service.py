"""Notification service for managing in-app notifications."""

from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId

from app.models.notification import (
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationAction,
    NOTIFICATION_COLLECTION,
)


class NotificationService:
    """Service for creating and managing notifications."""

    def __init__(self, db):
        self.db = db
        self.collection = db[NOTIFICATION_COLLECTION]

    async def create_notification(
        self,
        company_id: str,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        related_type: str | None = None,
        related_id: str | None = None,
        action_url: str | None = None,
        actions: list[dict] | None = None,
        icon: str | None = None,
        expires_in_hours: int | None = None,
    ) -> str:
        """
        Create a new notification.

        Returns:
            The ID of the created notification.
        """
        now = datetime.utcnow()

        notification_doc = {
            "company_id": company_id,
            "user_id": user_id,
            "type": notification_type.value,
            "priority": priority.value,
            "title": title,
            "message": message,
            "icon": icon,
            "related_type": related_type,
            "related_id": related_id,
            "action_url": action_url,
            "actions": actions or [],
            "is_read": False,
            "read_at": None,
            "is_dismissed": False,
            "dismissed_at": None,
            "expires_at": now + timedelta(hours=expires_in_hours) if expires_in_hours else None,
            "created_at": now,
        }

        result = await self.collection.insert_one(notification_doc)
        return str(result.inserted_id)

    async def notify_pending_approval(
        self,
        company_id: str,
        user_id: str,
        content_id: str,
        content_title: str,
        minutes_until_publish: int | None = None,
    ) -> str:
        """Notify user about content pending approval."""
        if minutes_until_publish:
            message = f"Treść '{content_title}' wymaga zatwierdzenia. Publikacja za {minutes_until_publish} minut."
        else:
            message = f"Treść '{content_title}' wymaga Twojego zatwierdzenia."

        return await self.create_notification(
            company_id=company_id,
            user_id=user_id,
            notification_type=NotificationType.PENDING_APPROVAL,
            title="Treść do zatwierdzenia",
            message=message,
            priority=NotificationPriority.HIGH,
            related_type="scheduled_content",
            related_id=content_id,
            action_url=f"/queue?highlight={content_id}",
            actions=[
                {"label": "Zatwierdź", "action_type": "approve", "action_data": {"content_id": content_id}},
                {"label": "Odrzuć", "action_type": "reject", "action_data": {"content_id": content_id}},
                {"label": "Zobacz", "action_type": "navigate", "action_url": f"/queue?highlight={content_id}"},
            ],
            icon="AlertCircle",
            expires_in_hours=24,
        )

    async def notify_content_published(
        self,
        company_id: str,
        user_id: str,
        content_id: str,
        content_title: str,
        platform: str,
    ) -> str:
        """Notify user that content was published."""
        return await self.create_notification(
            company_id=company_id,
            user_id=user_id,
            notification_type=NotificationType.CONTENT_PUBLISHED,
            title="Treść opublikowana",
            message=f"'{content_title}' została opublikowana na {platform}.",
            priority=NotificationPriority.NORMAL,
            related_type="scheduled_content",
            related_id=content_id,
            action_url=f"/queue?status=published",
            icon="CheckCircle",
            expires_in_hours=72,
        )

    async def notify_content_failed(
        self,
        company_id: str,
        user_id: str,
        content_id: str,
        content_title: str,
        error_message: str,
    ) -> str:
        """Notify user that content publication failed."""
        return await self.create_notification(
            company_id=company_id,
            user_id=user_id,
            notification_type=NotificationType.CONTENT_FAILED,
            title="Błąd publikacji",
            message=f"Nie udało się opublikować '{content_title}': {error_message[:100]}",
            priority=NotificationPriority.HIGH,
            related_type="scheduled_content",
            related_id=content_id,
            action_url=f"/queue?highlight={content_id}",
            icon="AlertTriangle",
            expires_in_hours=168,  # 1 week
        )

    async def notify_rule_generated(
        self,
        company_id: str,
        user_id: str,
        rule_id: str,
        rule_name: str,
        content_id: str,
    ) -> str:
        """Notify user that a rule generated new content."""
        return await self.create_notification(
            company_id=company_id,
            user_id=user_id,
            notification_type=NotificationType.RULE_GENERATED,
            title="Nowa treść wygenerowana",
            message=f"Automatyzacja '{rule_name}' wygenerowała nową treść.",
            priority=NotificationPriority.NORMAL,
            related_type="scheduled_content",
            related_id=content_id,
            action_url=f"/queue?highlight={content_id}",
            icon="Sparkles",
            expires_in_hours=48,
        )

    async def notify_rule_error(
        self,
        company_id: str,
        user_id: str,
        rule_id: str,
        rule_name: str,
        error_message: str,
    ) -> str:
        """Notify user that a rule encountered an error."""
        return await self.create_notification(
            company_id=company_id,
            user_id=user_id,
            notification_type=NotificationType.RULE_ERROR,
            title="Błąd automatyzacji",
            message=f"Automatyzacja '{rule_name}' napotkała błąd: {error_message[:100]}",
            priority=NotificationPriority.HIGH,
            related_type="schedule_rule",
            related_id=rule_id,
            action_url=f"/automation",
            icon="AlertTriangle",
            expires_in_hours=168,
        )

    async def notify_batch_completed(
        self,
        company_id: str,
        user_id: str,
        total_generated: int,
        total_scheduled: int,
    ) -> str:
        """Notify user that batch generation completed."""
        return await self.create_notification(
            company_id=company_id,
            user_id=user_id,
            notification_type=NotificationType.BATCH_COMPLETED,
            title="Batch ukończony",
            message=f"Wygenerowano {total_generated} treści, zaplanowano {total_scheduled}.",
            priority=NotificationPriority.NORMAL,
            action_url="/queue",
            icon="Rocket",
            expires_in_hours=48,
        )

    async def get_user_notifications(
        self,
        user_id: str,
        include_read: bool = False,
        include_dismissed: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Get notifications for a user."""
        query: dict[str, Any] = {"user_id": user_id}

        if not include_read:
            query["is_read"] = False
        if not include_dismissed:
            query["is_dismissed"] = False

        # Get total count
        total = await self.collection.count_documents(query)

        # Get notifications
        cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        notifications = await cursor.to_list(length=limit)

        # Convert ObjectId to string
        for n in notifications:
            n["id"] = str(n.pop("_id"))

        return notifications, total

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        return await self.collection.count_documents({
            "user_id": user_id,
            "is_read": False,
            "is_dismissed": False,
        })

    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read."""
        result = await self.collection.update_one(
            {"_id": ObjectId(notification_id), "user_id": user_id},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user."""
        result = await self.collection.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}},
        )
        return result.modified_count

    async def dismiss_notification(self, notification_id: str, user_id: str) -> bool:
        """Dismiss a notification."""
        result = await self.collection.update_one(
            {"_id": ObjectId(notification_id), "user_id": user_id},
            {"$set": {"is_dismissed": True, "dismissed_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def dismiss_all(self, user_id: str) -> int:
        """Dismiss all notifications for a user."""
        result = await self.collection.update_many(
            {"user_id": user_id, "is_dismissed": False},
            {"$set": {"is_dismissed": True, "dismissed_at": datetime.utcnow()}},
        )
        return result.modified_count

    async def delete_old_notifications(self, days: int = 30) -> int:
        """Delete notifications older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.collection.delete_many({
            "created_at": {"$lt": cutoff},
            "is_read": True,
        })
        return result.deleted_count

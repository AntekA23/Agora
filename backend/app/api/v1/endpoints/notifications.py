"""API endpoints for notifications."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationCountResponse,
    MarkReadRequest,
    MarkReadResponse,
    DismissRequest,
    DismissResponse,
    NotificationAction,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    include_read: bool = Query(False, description="Include read notifications"),
    include_dismissed: bool = Query(False, description="Include dismissed notifications"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get notifications for the current user."""
    user_id = str(current_user["_id"])

    service = NotificationService(db)
    notifications, total = await service.get_user_notifications(
        user_id=user_id,
        include_read=include_read,
        include_dismissed=include_dismissed,
        limit=limit,
        offset=offset,
    )

    unread_count = await service.get_unread_count(user_id)

    items = [
        NotificationResponse(
            id=n["id"],
            type=n["type"],
            priority=n["priority"],
            title=n["title"],
            message=n["message"],
            icon=n.get("icon"),
            related_type=n.get("related_type"),
            related_id=n.get("related_id"),
            action_url=n.get("action_url"),
            actions=[
                NotificationAction(**a) for a in n.get("actions", [])
            ],
            is_read=n["is_read"],
            read_at=n.get("read_at"),
            created_at=n["created_at"],
        )
        for n in notifications
    ]

    return NotificationListResponse(
        items=items,
        total=total,
        unread_count=unread_count,
    )


@router.get("/count", response_model=NotificationCountResponse)
async def get_notification_count(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get count of unread notifications."""
    user_id = str(current_user["_id"])

    service = NotificationService(db)
    unread_count = await service.get_unread_count(user_id)

    return NotificationCountResponse(unread_count=unread_count)


@router.post("/mark-read", response_model=MarkReadResponse)
async def mark_notifications_read(
    request: MarkReadRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Mark notifications as read."""
    user_id = str(current_user["_id"])
    service = NotificationService(db)

    if request.notification_ids:
        # Mark specific notifications
        count = 0
        for notification_id in request.notification_ids:
            if await service.mark_as_read(notification_id, user_id):
                count += 1
        return MarkReadResponse(marked_count=count)
    else:
        # Mark all as read
        count = await service.mark_all_as_read(user_id)
        return MarkReadResponse(marked_count=count)


@router.post("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_single_notification_read(
    notification_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Mark a single notification as read."""
    user_id = str(current_user["_id"])
    service = NotificationService(db)

    success = await service.mark_as_read(notification_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return MarkReadResponse(marked_count=1)


@router.post("/dismiss", response_model=DismissResponse)
async def dismiss_notifications(
    request: DismissRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Dismiss notifications."""
    user_id = str(current_user["_id"])
    service = NotificationService(db)

    if request.notification_ids:
        # Dismiss specific notifications
        count = 0
        for notification_id in request.notification_ids:
            if await service.dismiss_notification(notification_id, user_id):
                count += 1
        return DismissResponse(dismissed_count=count)
    else:
        # Dismiss all
        count = await service.dismiss_all(user_id)
        return DismissResponse(dismissed_count=count)


@router.delete("/{notification_id}")
async def dismiss_single_notification(
    notification_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Dismiss a single notification."""
    user_id = str(current_user["_id"])
    service = NotificationService(db)

    success = await service.dismiss_notification(notification_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return {"dismissed": True, "id": notification_id}

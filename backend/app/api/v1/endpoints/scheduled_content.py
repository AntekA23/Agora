"""API endpoints for scheduled content queue."""

from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, Database
from app.models.scheduled_content import ContentPlatform, ContentStatus, ContentType
from app.schemas.scheduled_content import (
    ApproveContentRequest,
    BulkActionRequest,
    BulkActionResponse,
    ScheduledContentCreate,
    ScheduledContentListResponse,
    ScheduledContentResponse,
    ScheduledContentStats,
    ScheduledContentUpdate,
)

router = APIRouter(prefix="/scheduled-content", tags=["scheduled-content"])


def _doc_to_response(doc: dict) -> ScheduledContentResponse:
    """Convert MongoDB document to response model."""
    return ScheduledContentResponse(
        id=str(doc["_id"]),
        company_id=doc["company_id"],
        created_by=doc["created_by"],
        title=doc["title"],
        content_type=doc["content_type"],
        platform=doc["platform"],
        content=doc.get("content", {}),
        media_urls=doc.get("media_urls", []),
        status=doc["status"],
        scheduled_for=doc.get("scheduled_for"),
        timezone=doc.get("timezone", "Europe/Warsaw"),
        published_at=doc.get("published_at"),
        source_task_id=doc.get("source_task_id"),
        source_conversation_id=doc.get("source_conversation_id"),
        source_rule_id=doc.get("source_rule_id"),
        platform_post_id=doc.get("platform_post_id"),
        platform_post_url=doc.get("platform_post_url"),
        engagement_stats=doc.get("engagement_stats"),
        error_message=doc.get("error_message"),
        retry_count=doc.get("retry_count", 0),
        requires_approval=doc.get("requires_approval", False),
        approved_by=doc.get("approved_by"),
        approved_at=doc.get("approved_at"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.get("", response_model=ScheduledContentListResponse)
async def list_scheduled_content(
    current_user: CurrentUser,
    db: Database,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: list[ContentStatus] | None = Query(None, alias="status"),
    platform: list[ContentPlatform] | None = Query(None),
    content_type: list[ContentType] | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    search: str | None = Query(None),
) -> ScheduledContentListResponse:
    """List scheduled content for current user's company."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Build query
    query: dict = {"company_id": current_user.company_id}

    if status_filter:
        query["status"] = {"$in": [s.value for s in status_filter]}
    if platform:
        query["platform"] = {"$in": [p.value for p in platform]}
    if content_type:
        query["content_type"] = {"$in": [ct.value for ct in content_type]}
    if date_from:
        query["scheduled_for"] = {"$gte": date_from}
    if date_to:
        if "scheduled_for" in query:
            query["scheduled_for"]["$lte"] = date_to
        else:
            query["scheduled_for"] = {"$lte": date_to}
    if search:
        query["title"] = {"$regex": search, "$options": "i"}

    # Get total count
    total = await db.scheduled_content.count_documents(query)

    # Get paginated items
    skip = (page - 1) * per_page
    cursor = (
        db.scheduled_content.find(query)
        .sort([("scheduled_for", 1), ("created_at", -1)])
        .skip(skip)
        .limit(per_page)
    )

    items = []
    async for doc in cursor:
        items.append(_doc_to_response(doc))

    return ScheduledContentListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/stats", response_model=ScheduledContentStats)
async def get_stats(
    current_user: CurrentUser,
    db: Database,
) -> ScheduledContentStats:
    """Get statistics for scheduled content."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company_id = current_user.company_id

    # Total count
    total = await db.scheduled_content.count_documents({"company_id": company_id})

    # Count by status
    status_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    by_status = {}
    async for doc in db.scheduled_content.aggregate(status_pipeline):
        by_status[doc["_id"]] = doc["count"]

    # Count by platform
    platform_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
    ]
    by_platform = {}
    async for doc in db.scheduled_content.aggregate(platform_pipeline):
        by_platform[doc["_id"]] = doc["count"]

    # This week counts
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    scheduled_this_week = await db.scheduled_content.count_documents({
        "company_id": company_id,
        "scheduled_for": {"$gte": week_start},
        "status": {"$in": ["scheduled", "pending_approval"]},
    })

    published_this_week = await db.scheduled_content.count_documents({
        "company_id": company_id,
        "published_at": {"$gte": week_start},
        "status": "published",
    })

    return ScheduledContentStats(
        total=total,
        by_status=by_status,
        by_platform=by_platform,
        scheduled_this_week=scheduled_this_week,
        published_this_week=published_this_week,
    )


@router.post("", response_model=ScheduledContentResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_content(
    data: ScheduledContentCreate,
    current_user: CurrentUser,
    db: Database,
) -> ScheduledContentResponse:
    """Add content to the queue."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    now = datetime.utcnow()

    # Determine initial status
    if data.scheduled_for:
        initial_status = (
            ContentStatus.PENDING_APPROVAL.value
            if data.requires_approval
            else ContentStatus.SCHEDULED.value
        )
    else:
        initial_status = ContentStatus.DRAFT.value

    doc = {
        "company_id": current_user.company_id,
        "created_by": current_user.id,
        "title": data.title,
        "content_type": data.content_type.value,
        "platform": data.platform.value,
        "content": data.content,
        "media_urls": data.media_urls,
        "status": initial_status,
        "scheduled_for": data.scheduled_for,
        "timezone": data.timezone,
        "published_at": None,
        "source_task_id": data.source_task_id,
        "source_conversation_id": data.source_conversation_id,
        "source_rule_id": None,
        "platform_post_id": None,
        "platform_post_url": None,
        "engagement_stats": None,
        "error_message": None,
        "retry_count": 0,
        "max_retries": 3,
        "requires_approval": data.requires_approval,
        "approved_by": None,
        "approved_at": None,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.scheduled_content.insert_one(doc)
    doc["_id"] = result.inserted_id

    return _doc_to_response(doc)


@router.get("/{content_id}", response_model=ScheduledContentResponse)
async def get_scheduled_content(
    content_id: str,
    current_user: CurrentUser,
    db: Database,
) -> ScheduledContentResponse:
    """Get a specific scheduled content item."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        doc = await db.scheduled_content.find_one({
            "_id": ObjectId(content_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    return _doc_to_response(doc)


@router.patch("/{content_id}", response_model=ScheduledContentResponse)
async def update_scheduled_content(
    content_id: str,
    data: ScheduledContentUpdate,
    current_user: CurrentUser,
    db: Database,
) -> ScheduledContentResponse:
    """Update scheduled content."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        doc = await db.scheduled_content.find_one({
            "_id": ObjectId(content_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    # Cannot update published content
    if doc["status"] == ContentStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update published content",
        )

    # Build update
    update_data = {"updated_at": datetime.utcnow()}

    if data.title is not None:
        update_data["title"] = data.title
    if data.content is not None:
        update_data["content"] = data.content
    if data.media_urls is not None:
        update_data["media_urls"] = data.media_urls
    if data.scheduled_for is not None:
        update_data["scheduled_for"] = data.scheduled_for
    if data.timezone is not None:
        update_data["timezone"] = data.timezone
    if data.status is not None:
        update_data["status"] = data.status.value
    if data.requires_approval is not None:
        update_data["requires_approval"] = data.requires_approval

    await db.scheduled_content.update_one(
        {"_id": ObjectId(content_id)},
        {"$set": update_data},
    )

    updated_doc = await db.scheduled_content.find_one({"_id": ObjectId(content_id)})
    return _doc_to_response(updated_doc)


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_content(
    content_id: str,
    current_user: CurrentUser,
    db: Database,
) -> None:
    """Delete scheduled content."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        result = await db.scheduled_content.delete_one({
            "_id": ObjectId(content_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")


@router.post("/{content_id}/approve", response_model=ScheduledContentResponse)
async def approve_content(
    content_id: str,
    data: ApproveContentRequest,
    current_user: CurrentUser,
    db: Database,
) -> ScheduledContentResponse:
    """Approve content for publishing."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        doc = await db.scheduled_content.find_one({
            "_id": ObjectId(content_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    if doc["status"] != ContentStatus.PENDING_APPROVAL.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is not pending approval",
        )

    now = datetime.utcnow()
    update_data = {
        "status": ContentStatus.SCHEDULED.value,
        "approved_by": current_user.id,
        "approved_at": now,
        "updated_at": now,
    }

    if data.scheduled_for:
        update_data["scheduled_for"] = data.scheduled_for

    await db.scheduled_content.update_one(
        {"_id": ObjectId(content_id)},
        {"$set": update_data},
    )

    updated_doc = await db.scheduled_content.find_one({"_id": ObjectId(content_id)})
    return _doc_to_response(updated_doc)


@router.post("/{content_id}/reject", response_model=ScheduledContentResponse)
async def reject_content(
    content_id: str,
    current_user: CurrentUser,
    db: Database,
) -> ScheduledContentResponse:
    """Reject content (move back to draft)."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        doc = await db.scheduled_content.find_one({
            "_id": ObjectId(content_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    if doc["status"] not in [ContentStatus.PENDING_APPROVAL.value, ContentStatus.SCHEDULED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content cannot be rejected in current status",
        )

    now = datetime.utcnow()
    await db.scheduled_content.update_one(
        {"_id": ObjectId(content_id)},
        {
            "$set": {
                "status": ContentStatus.DRAFT.value,
                "scheduled_for": None,
                "approved_by": None,
                "approved_at": None,
                "updated_at": now,
            }
        },
    )

    updated_doc = await db.scheduled_content.find_one({"_id": ObjectId(content_id)})
    return _doc_to_response(updated_doc)


@router.post("/{content_id}/publish", response_model=ScheduledContentResponse)
async def publish_content_now(
    content_id: str,
    current_user: CurrentUser,
    db: Database,
) -> ScheduledContentResponse:
    """Publish content immediately (marks as published without actual platform integration)."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        doc = await db.scheduled_content.find_one({
            "_id": ObjectId(content_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    if doc["status"] == ContentStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is already published",
        )

    if doc["status"] == ContentStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish failed content. Please retry or create new content.",
        )

    now = datetime.utcnow()

    # In Phase 1, we just mark as published (no actual platform integration yet)
    # Real publishing will be added in Phase 6
    update_data = {
        "status": ContentStatus.PUBLISHED.value,
        "published_at": now,
        "updated_at": now,
    }

    # If not approved yet, auto-approve
    if not doc.get("approved_by"):
        update_data["approved_by"] = current_user.id
        update_data["approved_at"] = now

    await db.scheduled_content.update_one(
        {"_id": ObjectId(content_id)},
        {"$set": update_data},
    )

    updated_doc = await db.scheduled_content.find_one({"_id": ObjectId(content_id)})
    return _doc_to_response(updated_doc)


@router.post("/bulk-action", response_model=BulkActionResponse)
async def bulk_action(
    data: BulkActionRequest,
    current_user: CurrentUser,
    db: Database,
) -> BulkActionResponse:
    """Perform bulk action on multiple content items."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    success_count = 0
    failed_count = 0
    failed_ids = []
    errors = {}

    for content_id in data.ids:
        try:
            obj_id = ObjectId(content_id)
            doc = await db.scheduled_content.find_one({
                "_id": obj_id,
                "company_id": current_user.company_id,
            })

            if not doc:
                failed_count += 1
                failed_ids.append(content_id)
                errors[content_id] = "Not found"
                continue

            now = datetime.utcnow()

            if data.action == "approve":
                if doc["status"] == ContentStatus.PENDING_APPROVAL.value:
                    await db.scheduled_content.update_one(
                        {"_id": obj_id},
                        {
                            "$set": {
                                "status": ContentStatus.SCHEDULED.value,
                                "approved_by": current_user.id,
                                "approved_at": now,
                                "updated_at": now,
                            }
                        },
                    )
                    success_count += 1
                else:
                    failed_count += 1
                    failed_ids.append(content_id)
                    errors[content_id] = "Not pending approval"

            elif data.action == "reject":
                if doc["status"] in [ContentStatus.PENDING_APPROVAL.value, ContentStatus.SCHEDULED.value]:
                    await db.scheduled_content.update_one(
                        {"_id": obj_id},
                        {
                            "$set": {
                                "status": ContentStatus.DRAFT.value,
                                "scheduled_for": None,
                                "updated_at": now,
                            }
                        },
                    )
                    success_count += 1
                else:
                    failed_count += 1
                    failed_ids.append(content_id)
                    errors[content_id] = "Cannot reject in current status"

            elif data.action == "delete":
                if doc["status"] != ContentStatus.PUBLISHED.value:
                    await db.scheduled_content.delete_one({"_id": obj_id})
                    success_count += 1
                else:
                    failed_count += 1
                    failed_ids.append(content_id)
                    errors[content_id] = "Cannot delete published content"

            elif data.action == "reschedule":
                if data.new_scheduled_for and doc["status"] != ContentStatus.PUBLISHED.value:
                    await db.scheduled_content.update_one(
                        {"_id": obj_id},
                        {
                            "$set": {
                                "scheduled_for": data.new_scheduled_for,
                                "updated_at": now,
                            }
                        },
                    )
                    success_count += 1
                else:
                    failed_count += 1
                    failed_ids.append(content_id)
                    errors[content_id] = "Cannot reschedule"

            else:
                failed_count += 1
                failed_ids.append(content_id)
                errors[content_id] = f"Unknown action: {data.action}"

        except Exception as e:
            failed_count += 1
            failed_ids.append(content_id)
            errors[content_id] = str(e)

    return BulkActionResponse(
        success_count=success_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        errors=errors,
    )

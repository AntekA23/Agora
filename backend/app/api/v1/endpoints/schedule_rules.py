"""API endpoints for content schedule rules."""

from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, Database
from app.models.schedule_rule import RuleFrequency
from app.schemas.schedule_rule import (
    GenerateNowRequest,
    GenerateNowResponse,
    ScheduleRuleCreate,
    ScheduleRuleListResponse,
    ScheduleRuleResponse,
    ScheduleRuleStats,
    ScheduleRuleUpdate,
)

router = APIRouter(prefix="/schedule-rules", tags=["schedule-rules"])


def _calculate_next_execution(schedule: dict, from_time: datetime | None = None) -> datetime:
    """Calculate the next execution time based on schedule config."""
    now = from_time or datetime.utcnow()
    frequency = schedule.get("frequency", "weekly")
    time_str = schedule.get("time", "08:00")
    hour, minute = map(int, time_str.split(":"))

    if frequency == RuleFrequency.DAILY.value:
        # Next day at specified time
        next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_exec <= now:
            next_exec += timedelta(days=1)
        return next_exec

    elif frequency == RuleFrequency.WEEKLY.value:
        days_of_week = schedule.get("days_of_week", [0])
        if not days_of_week:
            days_of_week = [0]

        # Find next matching day
        current_weekday = now.weekday()
        days_ahead = None

        for day in sorted(days_of_week):
            if day > current_weekday:
                days_ahead = day - current_weekday
                break
            elif day == current_weekday:
                # Check if time hasn't passed today
                today_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if today_exec > now:
                    days_ahead = 0
                    break

        if days_ahead is None:
            # Next week
            days_ahead = 7 - current_weekday + min(days_of_week)

        next_exec = now + timedelta(days=days_ahead)
        next_exec = next_exec.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return next_exec

    elif frequency == RuleFrequency.MONTHLY.value:
        day_of_month = schedule.get("day_of_month", 1)

        # Try this month
        try:
            next_exec = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            if next_exec <= now:
                # Next month
                if now.month == 12:
                    next_exec = next_exec.replace(year=now.year + 1, month=1)
                else:
                    next_exec = next_exec.replace(month=now.month + 1)
        except ValueError:
            # Day doesn't exist in month, use last day
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            next_exec = next_month - timedelta(days=1)
            next_exec = next_exec.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return next_exec

    # Default fallback
    return now + timedelta(days=1)


def _doc_to_response(doc: dict, queue_count: int = 0) -> ScheduleRuleResponse:
    """Convert MongoDB document to response model."""
    return ScheduleRuleResponse(
        id=str(doc["_id"]),
        company_id=doc["company_id"],
        created_by=doc["created_by"],
        name=doc["name"],
        description=doc.get("description"),
        content_type=doc["content_type"],
        platform=doc["platform"],
        content_template=doc.get("content_template", {}),
        schedule=doc.get("schedule", {}),
        approval_mode=doc.get("approval_mode", "require_approval"),
        notify_before_publish=doc.get("notify_before_publish", True),
        notification_minutes=doc.get("notification_minutes", 60),
        fallback_on_no_response=doc.get("fallback_on_no_response", "publish"),
        is_active=doc.get("is_active", True),
        last_executed=doc.get("last_executed"),
        next_execution=doc.get("next_execution"),
        last_error=doc.get("last_error"),
        max_queue_size=doc.get("max_queue_size", 4),
        total_generated=doc.get("total_generated", 0),
        total_published=doc.get("total_published", 0),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        queue_count=queue_count,
    )


@router.get("", response_model=ScheduleRuleListResponse)
async def list_schedule_rules(
    current_user: CurrentUser,
    db: Database,
    is_active: bool | None = Query(None),
) -> ScheduleRuleListResponse:
    """List all schedule rules for current user's company."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    query: dict = {"company_id": current_user.company_id}
    if is_active is not None:
        query["is_active"] = is_active

    cursor = db.schedule_rules.find(query).sort("created_at", -1)

    items = []
    async for doc in cursor:
        # Get queue count for this rule
        queue_count = await db.scheduled_content.count_documents({
            "source_rule_id": str(doc["_id"]),
            "status": {"$in": ["draft", "queued", "scheduled", "pending_approval"]},
        })
        items.append(_doc_to_response(doc, queue_count))

    # Count active/paused
    active_count = sum(1 for item in items if item.is_active)
    paused_count = len(items) - active_count

    return ScheduleRuleListResponse(
        items=items,
        total=len(items),
        active_count=active_count,
        paused_count=paused_count,
    )


@router.get("/stats", response_model=ScheduleRuleStats)
async def get_stats(
    current_user: CurrentUser,
    db: Database,
) -> ScheduleRuleStats:
    """Get statistics for schedule rules."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company_id = current_user.company_id

    # Count rules
    total_rules = await db.schedule_rules.count_documents({"company_id": company_id})
    active_rules = await db.schedule_rules.count_documents({
        "company_id": company_id,
        "is_active": True,
    })
    paused_rules = total_rules - active_rules

    # Aggregate totals
    pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {
            "_id": None,
            "total_generated": {"$sum": "$total_generated"},
            "total_published": {"$sum": "$total_published"},
        }},
    ]
    totals = {"total_generated": 0, "total_published": 0}
    async for doc in db.schedule_rules.aggregate(pipeline):
        totals = doc

    # Get next executions
    cursor = db.schedule_rules.find({
        "company_id": company_id,
        "is_active": True,
        "next_execution": {"$ne": None},
    }).sort("next_execution", 1).limit(5)

    next_executions = []
    async for doc in cursor:
        next_executions.append({
            "rule_id": str(doc["_id"]),
            "rule_name": doc["name"],
            "next_execution": doc["next_execution"].isoformat() if doc.get("next_execution") else None,
        })

    return ScheduleRuleStats(
        total_rules=total_rules,
        active_rules=active_rules,
        paused_rules=paused_rules,
        total_generated=totals.get("total_generated", 0),
        total_published=totals.get("total_published", 0),
        next_executions=next_executions,
    )


@router.post("", response_model=ScheduleRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule_rule(
    data: ScheduleRuleCreate,
    current_user: CurrentUser,
    db: Database,
) -> ScheduleRuleResponse:
    """Create a new schedule rule."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    now = datetime.utcnow()

    # Calculate next execution
    schedule_dict = data.schedule.model_dump()
    next_execution = _calculate_next_execution(schedule_dict)

    doc = {
        "company_id": current_user.company_id,
        "created_by": current_user.id,
        "name": data.name,
        "description": data.description,
        "content_type": data.content_type.value,
        "platform": data.platform.value,
        "content_template": data.content_template.model_dump(),
        "schedule": schedule_dict,
        "approval_mode": data.approval_mode.value,
        "notify_before_publish": data.notify_before_publish,
        "notification_minutes": data.notification_minutes,
        "fallback_on_no_response": data.fallback_on_no_response,
        "is_active": True,
        "last_executed": None,
        "next_execution": next_execution,
        "last_error": None,
        "max_queue_size": data.max_queue_size,
        "total_generated": 0,
        "total_published": 0,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.schedule_rules.insert_one(doc)
    doc["_id"] = result.inserted_id

    return _doc_to_response(doc, 0)


@router.get("/{rule_id}", response_model=ScheduleRuleResponse)
async def get_schedule_rule(
    rule_id: str,
    current_user: CurrentUser,
    db: Database,
) -> ScheduleRuleResponse:
    """Get a specific schedule rule."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        doc = await db.schedule_rules.find_one({
            "_id": ObjectId(rule_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    # Get queue count
    queue_count = await db.scheduled_content.count_documents({
        "source_rule_id": rule_id,
        "status": {"$in": ["draft", "queued", "scheduled", "pending_approval"]},
    })

    return _doc_to_response(doc, queue_count)


@router.patch("/{rule_id}", response_model=ScheduleRuleResponse)
async def update_schedule_rule(
    rule_id: str,
    data: ScheduleRuleUpdate,
    current_user: CurrentUser,
    db: Database,
) -> ScheduleRuleResponse:
    """Update a schedule rule."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        doc = await db.schedule_rules.find_one({
            "_id": ObjectId(rule_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    update_data: dict = {"updated_at": datetime.utcnow()}

    if data.name is not None:
        update_data["name"] = data.name
    if data.description is not None:
        update_data["description"] = data.description
    if data.content_template is not None:
        update_data["content_template"] = data.content_template.model_dump()
    if data.schedule is not None:
        schedule_dict = data.schedule.model_dump()
        update_data["schedule"] = schedule_dict
        # Recalculate next execution
        update_data["next_execution"] = _calculate_next_execution(schedule_dict)
    if data.approval_mode is not None:
        update_data["approval_mode"] = data.approval_mode.value
    if data.notify_before_publish is not None:
        update_data["notify_before_publish"] = data.notify_before_publish
    if data.notification_minutes is not None:
        update_data["notification_minutes"] = data.notification_minutes
    if data.fallback_on_no_response is not None:
        update_data["fallback_on_no_response"] = data.fallback_on_no_response
    if data.max_queue_size is not None:
        update_data["max_queue_size"] = data.max_queue_size

    await db.schedule_rules.update_one(
        {"_id": ObjectId(rule_id)},
        {"$set": update_data},
    )

    updated_doc = await db.schedule_rules.find_one({"_id": ObjectId(rule_id)})

    # Get queue count
    queue_count = await db.scheduled_content.count_documents({
        "source_rule_id": rule_id,
        "status": {"$in": ["draft", "queued", "scheduled", "pending_approval"]},
    })

    return _doc_to_response(updated_doc, queue_count)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule_rule(
    rule_id: str,
    current_user: CurrentUser,
    db: Database,
) -> None:
    """Delete a schedule rule."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        result = await db.schedule_rules.delete_one({
            "_id": ObjectId(rule_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")


@router.post("/{rule_id}/toggle", response_model=ScheduleRuleResponse)
async def toggle_rule(
    rule_id: str,
    current_user: CurrentUser,
    db: Database,
) -> ScheduleRuleResponse:
    """Toggle rule active status (pause/resume)."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        doc = await db.schedule_rules.find_one({
            "_id": ObjectId(rule_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    new_active = not doc.get("is_active", True)
    update_data = {
        "is_active": new_active,
        "updated_at": datetime.utcnow(),
    }

    # If activating, recalculate next execution
    if new_active:
        update_data["next_execution"] = _calculate_next_execution(doc.get("schedule", {}))
        update_data["last_error"] = None

    await db.schedule_rules.update_one(
        {"_id": ObjectId(rule_id)},
        {"$set": update_data},
    )

    updated_doc = await db.schedule_rules.find_one({"_id": ObjectId(rule_id)})

    # Get queue count
    queue_count = await db.scheduled_content.count_documents({
        "source_rule_id": rule_id,
        "status": {"$in": ["draft", "queued", "scheduled", "pending_approval"]},
    })

    return _doc_to_response(updated_doc, queue_count)


@router.post("/{rule_id}/generate-now", response_model=GenerateNowResponse)
async def generate_now(
    rule_id: str,
    data: GenerateNowRequest,
    current_user: CurrentUser,
    db: Database,
) -> GenerateNowResponse:
    """Force generation of content from this rule now."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        doc = await db.schedule_rules.find_one({
            "_id": ObjectId(rule_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    # Check queue size
    queue_count = await db.scheduled_content.count_documents({
        "source_rule_id": rule_id,
        "status": {"$in": ["draft", "queued", "scheduled", "pending_approval"]},
    })

    if queue_count >= doc.get("max_queue_size", 4):
        return GenerateNowResponse(
            success=False,
            error=f"Kolejka jest pełna ({queue_count}/{doc.get('max_queue_size', 4)}). Usuń lub opublikuj istniejące treści.",
        )

    # Import here to avoid circular imports
    from app.services.scheduling.rule_executor import RuleExecutor

    executor = RuleExecutor(db)
    try:
        content_id = await executor.execute_rule(doc, schedule_for=data.schedule_for)
        return GenerateNowResponse(
            success=True,
            scheduled_content_id=content_id,
        )
    except Exception as e:
        return GenerateNowResponse(
            success=False,
            error=str(e),
        )

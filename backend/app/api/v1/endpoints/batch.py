"""API endpoints for batch content generation."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, Database
from app.schemas.batch import (
    BatchGenerationRequest,
    BatchGenerationResponse,
    BatchStatsResponse,
    GeneratedItem,
    GeneratedItemContent,
    ScheduledItem,
)
from app.services.scheduling import BatchGenerator

router = APIRouter(prefix="/batch", tags=["batch"])


@router.post("/generate", response_model=BatchGenerationResponse)
async def generate_batch(
    request: BatchGenerationRequest,
    db: Database,
    current_user: CurrentUser,
):
    """
    Generate a batch of content.

    This endpoint generates multiple pieces of content at once based on a theme.
    Content can be automatically scheduled or saved as drafts.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company_id = current_user.company_id
    user_id = current_user.id

    generator = BatchGenerator(db)

    # Prepare date range
    date_range = None
    if request.date_range:
        date_range = {
            "start": request.date_range.start,
            "end": request.date_range.end,
        }

    result = await generator.generate_batch(
        company_id=company_id,
        user_id=user_id,
        content_type=request.content_type,
        platform=request.platform,
        count=request.count,
        theme=request.theme,
        variety=request.variety,
        date_range=date_range,
        auto_schedule=request.auto_schedule,
        require_approval=request.require_approval,
    )

    # Convert to response model
    generated_items = []
    for item in result.get("generated_items", []):
        content = item.get("content")
        content_model = None
        if content:
            content_model = GeneratedItemContent(
                text=content.get("text"),
                caption=content.get("caption"),
                hashtags=content.get("hashtags"),
                error=content.get("error"),
            )

        generated_items.append(
            GeneratedItem(
                index=item["index"],
                prompt=item["prompt"],
                content=content_model,
                status=item["status"],
                error=item.get("error"),
            )
        )

    scheduled_items = [
        ScheduledItem(
            id=item["id"],
            title=item["title"],
            scheduled_for=item.get("scheduled_for"),
            status=item["status"],
        )
        for item in result.get("scheduled_items", [])
    ]

    return BatchGenerationResponse(
        total_requested=result["total_requested"],
        total_generated=result["total_generated"],
        total_failed=result["total_failed"],
        total_scheduled=result["total_scheduled"],
        generated_items=generated_items,
        scheduled_items=scheduled_items,
    )


@router.get("/stats", response_model=BatchStatsResponse)
async def get_batch_stats(
    db: Database,
    current_user: CurrentUser,
):
    """
    Get batch generation statistics for the company.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company_id = current_user.company_id

    # Count scheduled content (approximation of batch stats)
    # In production, we'd track batches separately
    pipeline = [
        {"$match": {"company_id": company_id}},
        {
            "$group": {
                "_id": None,
                "total_items": {"$sum": 1},
                "scheduled": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "scheduled"]}, 1, 0]
                    }
                },
                "published": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "published"]}, 1, 0]
                    }
                },
            }
        },
    ]

    stats = await db.scheduled_content.aggregate(pipeline).to_list(length=1)

    if not stats:
        return BatchStatsResponse(
            total_batches=0,
            total_items_generated=0,
            total_items_scheduled=0,
            total_items_published=0,
            average_batch_size=0.0,
            most_used_platform=None,
        )

    stats = stats[0]

    # Get most used platform
    platform_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1},
    ]
    platform_stats = await db.scheduled_content.aggregate(platform_pipeline).to_list(length=1)
    most_used = platform_stats[0]["_id"] if platform_stats else None

    return BatchStatsResponse(
        total_batches=stats.get("total_items", 0) // 5,  # Rough estimate
        total_items_generated=stats.get("total_items", 0),
        total_items_scheduled=stats.get("scheduled", 0),
        total_items_published=stats.get("published", 0),
        average_batch_size=5.0,  # Default
        most_used_platform=most_used,
    )


@router.delete("/scheduled/{content_id}")
async def remove_from_batch(
    content_id: str,
    db: Database,
    current_user: CurrentUser,
):
    """
    Remove a single item from scheduled batch content.
    """
    from bson import ObjectId

    company_id = current_user.company_id

    result = await db.scheduled_content.delete_one({
        "_id": ObjectId(content_id),
        "company_id": company_id,
        "status": {"$in": ["draft", "queued", "scheduled", "pending_approval"]},
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or cannot be deleted",
        )

    return {"deleted": True, "id": content_id}

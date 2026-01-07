"""A/B Testing Experiments API endpoints."""

from datetime import datetime
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.agents.ab_testing import (
    ab_testing_service,
    Experiment,
    ExperimentStatus,
    Variant,
    VariantMetrics,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])


# ============================================================================
# SCHEMAS
# ============================================================================


class VariantCreate(BaseModel):
    """Schema for creating a variant."""
    name: str = Field(..., min_length=1)
    content: dict[str, Any] = Field(..., description="Variant content (e.g., post text, image url)")
    weight: float = Field(default=0.5, ge=0, le=1, description="Traffic allocation")


class ExperimentCreate(BaseModel):
    """Schema for creating an experiment."""
    name: str = Field(..., min_length=1)
    description: str = ""
    agent: str = Field(..., description="Agent: instagram_specialist, copywriter")
    variants: list[VariantCreate] = Field(..., min_length=2, max_length=5)
    min_sample_size: int = Field(default=100, ge=10)


class VariantResponse(BaseModel):
    """Variant response schema."""
    id: str
    name: str
    content: dict[str, Any]
    weight: float
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    conversion_rate: float
    avg_feedback: float | None


class ExperimentResponse(BaseModel):
    """Experiment response schema."""
    id: str
    name: str
    description: str
    company_id: str
    agent: str
    status: str
    variants: list[VariantResponse]
    winner_variant_id: str | None
    created_at: str
    started_at: str | None
    ended_at: str | None


class ExperimentStats(BaseModel):
    """Experiment statistics."""
    id: str
    name: str
    status: str
    total_impressions: int
    total_clicks: int
    total_conversions: int
    overall_ctr: float
    overall_conversion_rate: float
    ready_for_decision: bool
    has_winner: bool
    winner: dict[str, Any] | None


class RecordEventRequest(BaseModel):
    """Request to record an event."""
    variant_id: str
    event_type: str = Field(..., description="Event type: impression, click, conversion, feedback")
    rating: int | None = Field(default=None, ge=1, le=5, description="Rating for feedback events")


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    data: ExperimentCreate,
    current_user: CurrentUser,
    db: Database,
) -> ExperimentResponse:
    """Create a new A/B testing experiment."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    # Validate variants have unique names
    names = [v.name for v in data.variants]
    if len(names) != len(set(names)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Variant names must be unique")

    # Create experiment
    experiment_id = str(ObjectId())
    variants_data = [
        {
            "id": str(ObjectId()),
            "name": v.name,
            "content": v.content,
            "weight": v.weight,
        }
        for v in data.variants
    ]

    experiment = ab_testing_service.create_experiment(
        experiment_id=experiment_id,
        name=data.name,
        company_id=current_user.company_id,
        agent=data.agent,
        variants=variants_data,
        description=data.description,
        min_sample_size=data.min_sample_size,
    )

    # Store in database
    experiment_doc = {
        "_id": ObjectId(experiment_id),
        "name": experiment.name,
        "description": experiment.description,
        "company_id": current_user.company_id,
        "agent": experiment.agent,
        "status": experiment.status.value,
        "variants": [
            {
                "id": v.id,
                "name": v.name,
                "content": v.content,
                "weight": v.weight,
                "metrics": {
                    "impressions": 0,
                    "clicks": 0,
                    "conversions": 0,
                    "feedback_count": 0,
                    "feedback_sum": 0,
                },
            }
            for v in experiment.variants
        ],
        "winner_variant_id": None,
        "min_sample_size": experiment.min_sample_size,
        "created_at": experiment.created_at,
        "started_at": None,
        "ended_at": None,
        "created_by": current_user.id,
    }
    await db.experiments.insert_one(experiment_doc)

    return _format_experiment_response(experiment_doc)


@router.get("", response_model=list[ExperimentStats])
async def list_experiments(
    current_user: CurrentUser,
    db: Database,
    status_filter: str | None = Query(None, alias="status"),
    agent: str | None = Query(None),
) -> list[ExperimentStats]:
    """List all experiments for the company."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    query: dict = {"company_id": current_user.company_id}
    if status_filter:
        query["status"] = status_filter
    if agent:
        query["agent"] = agent

    experiments = []
    async for doc in db.experiments.find(query).sort("created_at", -1):
        exp = _doc_to_experiment(doc)
        summary = ab_testing_service.get_experiment_summary(exp)
        experiments.append(ExperimentStats(**summary))

    return experiments


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    current_user: CurrentUser,
    db: Database,
) -> ExperimentResponse:
    """Get experiment details."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    doc = await db.experiments.find_one({
        "_id": ObjectId(experiment_id),
        "company_id": current_user.company_id,
    })

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    return _format_experiment_response(doc)


@router.post("/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Start an experiment."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    result = await db.experiments.update_one(
        {
            "_id": ObjectId(experiment_id),
            "company_id": current_user.company_id,
            "status": ExperimentStatus.DRAFT.value,
        },
        {
            "$set": {
                "status": ExperimentStatus.RUNNING.value,
                "started_at": datetime.utcnow(),
            }
        },
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment not found or cannot be started",
        )

    return {"status": "started", "experiment_id": experiment_id}


@router.post("/{experiment_id}/pause")
async def pause_experiment(
    experiment_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Pause a running experiment."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    result = await db.experiments.update_one(
        {
            "_id": ObjectId(experiment_id),
            "company_id": current_user.company_id,
            "status": ExperimentStatus.RUNNING.value,
        },
        {"$set": {"status": ExperimentStatus.PAUSED.value}},
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment not found or not running",
        )

    return {"status": "paused", "experiment_id": experiment_id}


@router.post("/{experiment_id}/complete")
async def complete_experiment(
    experiment_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Complete an experiment and determine winner."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    doc = await db.experiments.find_one({
        "_id": ObjectId(experiment_id),
        "company_id": current_user.company_id,
    })

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    if doc["status"] not in [ExperimentStatus.RUNNING.value, ExperimentStatus.PAUSED.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment cannot be completed")

    # Determine winner
    experiment = _doc_to_experiment(doc)
    winner_id = ab_testing_service.determine_winner(experiment)

    await db.experiments.update_one(
        {"_id": ObjectId(experiment_id)},
        {
            "$set": {
                "status": ExperimentStatus.COMPLETED.value,
                "winner_variant_id": winner_id,
                "ended_at": datetime.utcnow(),
            }
        },
    )

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "winner_variant_id": winner_id,
    }


@router.post("/{experiment_id}/event")
async def record_event(
    experiment_id: str,
    data: RecordEventRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Record an event (impression, click, conversion, feedback) for a variant."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    # Validate event type
    valid_events = ["impression", "click", "conversion", "feedback"]
    if data.event_type not in valid_events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type. Must be one of: {valid_events}",
        )

    if data.event_type == "feedback" and data.rating is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating required for feedback events",
        )

    # Build update
    update_field = f"variants.$.metrics.{data.event_type}s"
    if data.event_type == "feedback":
        update = {
            "$inc": {
                "variants.$.metrics.feedback_count": 1,
                "variants.$.metrics.feedback_sum": data.rating,
            }
        }
    else:
        update = {"$inc": {update_field: 1}}

    result = await db.experiments.update_one(
        {
            "_id": ObjectId(experiment_id),
            "company_id": current_user.company_id,
            "status": ExperimentStatus.RUNNING.value,
            "variants.id": data.variant_id,
        },
        update,
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment not found, not running, or variant not found",
        )

    return {"status": "recorded", "event_type": data.event_type, "variant_id": data.variant_id}


@router.get("/{experiment_id}/select-variant")
async def select_variant(
    experiment_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Select a variant for the current user based on traffic allocation.

    Call this when showing content to a user to get which variant to display.
    Don't forget to record an impression after showing the content.
    """
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    doc = await db.experiments.find_one({
        "_id": ObjectId(experiment_id),
        "company_id": current_user.company_id,
    })

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    experiment = _doc_to_experiment(doc)
    selected = ab_testing_service.select_variant(experiment)

    return {
        "variant_id": selected.id,
        "variant_name": selected.name,
        "content": selected.content,
    }


@router.get("/{experiment_id}/stats")
async def get_experiment_stats(
    experiment_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Get detailed statistics for an experiment."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    doc = await db.experiments.find_one({
        "_id": ObjectId(experiment_id),
        "company_id": current_user.company_id,
    })

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    experiment = _doc_to_experiment(doc)
    return ab_testing_service.calculate_statistics(experiment)


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    experiment_id: str,
    current_user: CurrentUser,
    db: Database,
) -> None:
    """Delete an experiment (only if draft or cancelled)."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    result = await db.experiments.delete_one({
        "_id": ObjectId(experiment_id),
        "company_id": current_user.company_id,
        "status": {"$in": [ExperimentStatus.DRAFT.value, ExperimentStatus.CANCELLED.value]},
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment not found or cannot be deleted (must be draft or cancelled)",
        )


# ============================================================================
# HELPERS
# ============================================================================


def _doc_to_experiment(doc: dict) -> Experiment:
    """Convert MongoDB document to Experiment object."""
    variants = []
    for v in doc["variants"]:
        metrics = v.get("metrics", {})
        variants.append(Variant(
            id=v["id"],
            name=v["name"],
            content=v["content"],
            weight=v.get("weight", 0.5),
            metrics=VariantMetrics(
                impressions=metrics.get("impressions", 0),
                clicks=metrics.get("clicks", 0),
                conversions=metrics.get("conversions", 0),
                feedback_count=metrics.get("feedback_count", 0),
                feedback_sum=metrics.get("feedback_sum", 0),
            ),
        ))

    return Experiment(
        id=str(doc["_id"]),
        name=doc["name"],
        description=doc.get("description", ""),
        company_id=doc["company_id"],
        agent=doc["agent"],
        variants=variants,
        status=ExperimentStatus(doc["status"]),
        winner_variant_id=doc.get("winner_variant_id"),
        created_at=doc["created_at"],
        started_at=doc.get("started_at"),
        ended_at=doc.get("ended_at"),
        min_sample_size=doc.get("min_sample_size", 100),
    )


def _format_experiment_response(doc: dict) -> ExperimentResponse:
    """Format experiment document for API response."""
    variants = []
    for v in doc["variants"]:
        metrics = v.get("metrics", {})
        impressions = metrics.get("impressions", 0)
        clicks = metrics.get("clicks", 0)
        conversions = metrics.get("conversions", 0)
        fb_count = metrics.get("feedback_count", 0)
        fb_sum = metrics.get("feedback_sum", 0)

        variants.append(VariantResponse(
            id=v["id"],
            name=v["name"],
            content=v["content"],
            weight=v.get("weight", 0.5),
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            ctr=round(clicks / impressions * 100, 2) if impressions > 0 else 0,
            conversion_rate=round(conversions / impressions * 100, 2) if impressions > 0 else 0,
            avg_feedback=round(fb_sum / fb_count, 2) if fb_count > 0 else None,
        ))

    return ExperimentResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        description=doc.get("description", ""),
        company_id=doc["company_id"],
        agent=doc["agent"],
        status=doc["status"],
        variants=variants,
        winner_variant_id=doc.get("winner_variant_id"),
        created_at=doc["created_at"].isoformat(),
        started_at=doc["started_at"].isoformat() if doc.get("started_at") else None,
        ended_at=doc["ended_at"].isoformat() if doc.get("ended_at") else None,
    )

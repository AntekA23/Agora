"""Autonomous Goals API endpoints."""

from datetime import datetime
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.agents.goals import (
    GoalAgent,
    GoalTracker,
    GoalStatus,
)

router = APIRouter(prefix="/goals", tags=["goals"])


# ============================================================================
# SCHEMAS
# ============================================================================


class GoalCreateRequest(BaseModel):
    """Request to create a new goal."""
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    category: str = Field(..., pattern="^(marketing|sales|finance|hr|support)$")
    target_metric: str = ""
    target_value: float | None = None
    deadline: datetime | None = None
    priority: int = Field(default=3, ge=1, le=5)


class GoalStepResponse(BaseModel):
    """Response schema for a goal step."""
    id: str
    order: int
    description: str
    status: str
    agent_type: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict = {}
    error: str | None = None


class GoalResponse(BaseModel):
    """Response schema for a goal."""
    id: str
    title: str
    description: str
    category: str
    target_metric: str
    target_value: float | None = None
    current_value: float | None = None
    deadline: datetime | None = None
    status: str
    priority: int
    steps: list[GoalStepResponse] = []
    research_data: dict = {}
    strategy: dict = {}
    progress_percentage: float = 0.0
    created_at: datetime
    updated_at: datetime


class GoalListResponse(BaseModel):
    """Response for list of goals."""
    goals: list[GoalResponse]
    total: int


class GoalStatisticsResponse(BaseModel):
    """Response for goal statistics."""
    total_goals: int
    by_status: dict[str, int]
    by_category: dict[str, dict]
    average_completion_days: float | None
    active_count: int
    success_rate: float


# ============================================================================
# GOAL CRUD ENDPOINTS
# ============================================================================


@router.post("", response_model=GoalResponse)
async def create_goal(
    data: GoalCreateRequest,
    current_user: CurrentUser,
    db: Database,
) -> GoalResponse:
    """Create a new autonomous goal.

    This will:
    1. Research best practices and strategies
    2. Create an execution plan
    3. Generate concrete steps

    The goal starts in DRAFT status.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    agent = GoalAgent(db)

    goal = await agent.create_goal(
        company_id=current_user.company_id,
        title=data.title,
        description=data.description,
        category=data.category,
        target_metric=data.target_metric,
        target_value=data.target_value,
        deadline=data.deadline,
        priority=data.priority,
    )

    return _goal_to_response(goal)


@router.get("", response_model=GoalListResponse)
async def get_goals(
    current_user: CurrentUser,
    db: Database,
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> GoalListResponse:
    """Get goals for the company."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    agent = GoalAgent(db)

    status_enum = GoalStatus(status_filter) if status_filter else None

    goals = await agent.get_goals(
        company_id=current_user.company_id,
        status=status_enum,
        category=category,
        limit=limit,
    )

    return GoalListResponse(
        goals=[_goal_to_response(g) for g in goals],
        total=len(goals),
    )


@router.get("/statistics", response_model=GoalStatisticsResponse)
async def get_goal_statistics(
    current_user: CurrentUser,
    db: Database,
) -> GoalStatisticsResponse:
    """Get statistics about company goals."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    tracker = GoalTracker(db)
    stats = await tracker.get_goal_statistics(current_user.company_id)

    return GoalStatisticsResponse(**stats)


@router.get("/recommend")
async def get_recommended_goal(
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Get recommendation for which goal to focus on next."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    tracker = GoalTracker(db)
    return await tracker.recommend_next_goal(current_user.company_id)


@router.get("/deadlines")
async def check_deadlines(
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Check for goals with approaching deadlines."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    tracker = GoalTracker(db)

    approaching = await tracker.check_deadlines(current_user.company_id)
    overdue = await tracker.get_overdue_goals(current_user.company_id)

    return {
        "approaching_deadline": approaching,
        "overdue": overdue,
        "total_at_risk": len([g for g in approaching if g.get("at_risk")]) + len(overdue),
    }


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: str,
    current_user: CurrentUser,
    db: Database,
) -> GoalResponse:
    """Get a specific goal by ID."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    agent = GoalAgent(db)
    goal = await agent.get_goal(goal_id, current_user.company_id)

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return _goal_to_response(goal)


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Delete a goal."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    result = await db.goals.delete_one({
        "_id": ObjectId(goal_id),
        "company_id": current_user.company_id,
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return {"status": "deleted", "goal_id": goal_id}


# ============================================================================
# GOAL EXECUTION ENDPOINTS
# ============================================================================


@router.post("/{goal_id}/start")
async def start_goal(
    goal_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Start executing a goal.

    Changes status from DRAFT to ACTIVE.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    agent = GoalAgent(db)
    goal = await agent.start_goal(goal_id, current_user.company_id)

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return {
        "status": "started",
        "goal_id": goal_id,
        "goal_status": goal.status.value,
    }


@router.post("/{goal_id}/pause")
async def pause_goal(
    goal_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Pause a running goal."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    agent = GoalAgent(db)
    goal = await agent.pause_goal(goal_id, current_user.company_id)

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found or not running",
        )

    return {
        "status": "paused",
        "goal_id": goal_id,
        "goal_status": goal.status.value,
    }


@router.post("/{goal_id}/execute-step")
async def execute_next_step(
    goal_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Execute the next pending step in the goal.

    This is the manual way to advance a goal.
    Steps can also be executed automatically by the scheduler.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    agent = GoalAgent(db)
    result = await agent.execute_next_step(goal_id, current_user.company_id)

    if not result.get("success") and "not found" in result.get("error", "").lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error"),
        )

    return result


@router.get("/{goal_id}/progress")
async def get_progress_report(
    goal_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Generate a progress report for the goal."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    agent = GoalAgent(db)
    result = await agent.get_progress_report(goal_id, current_user.company_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Goal not found"),
        )

    return result


# ============================================================================
# BATCH PROCESSING ENDPOINTS
# ============================================================================


@router.post("/process-all")
async def process_all_goals(
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Process all active goals - execute next steps.

    This endpoint triggers step execution for all active goals.
    Typically called by a scheduler or manually.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    tracker = GoalTracker(db)
    result = await tracker.process_active_goals(current_user.company_id)

    return result


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _goal_to_response(goal) -> GoalResponse:
    """Convert Goal model to response schema."""
    # Calculate progress percentage
    total_steps = len(goal.steps)
    completed_steps = sum(1 for s in goal.steps if s.status == "completed")
    progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0

    return GoalResponse(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        category=goal.category,
        target_metric=goal.target_metric,
        target_value=goal.target_value,
        current_value=goal.current_value,
        deadline=goal.deadline,
        status=goal.status.value if hasattr(goal.status, 'value') else goal.status,
        priority=goal.priority,
        steps=[GoalStepResponse(**s.model_dump()) for s in goal.steps],
        research_data=goal.research_data,
        strategy=goal.strategy,
        progress_percentage=progress,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )

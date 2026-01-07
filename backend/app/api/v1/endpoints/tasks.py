from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, Database
from app.schemas.task import TaskResponse, TaskListResponse
from app.schemas.feedback import (
    TaskFeedbackInput,
    TaskFeedbackResponse,
    FeedbackStatsResponse,
    AgentFeedbackStats,
)
from app.services.task_queue import get_task_queue
from app.services.agents.memory import memory_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: CurrentUser,
    db: Database,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    department: str | None = Query(None),
    agent: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
) -> TaskListResponse:
    """List tasks for current user's company."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Build query
    query: dict = {"company_id": current_user.company_id}

    if department:
        query["department"] = department
    if agent:
        query["agent"] = agent
    if status_filter:
        query["status"] = status_filter

    # Get total count
    total = await db.tasks.count_documents(query)

    # Get paginated tasks
    skip = (page - 1) * per_page
    cursor = db.tasks.find(query).sort("created_at", -1).skip(skip).limit(per_page)

    tasks = []
    async for task in cursor:
        tasks.append(TaskResponse(
            id=str(task["_id"]),
            company_id=task["company_id"],
            user_id=task["user_id"],
            department=task["department"],
            agent=task["agent"],
            type=task["type"],
            input=task["input"],
            output=task.get("output"),
            status=task["status"],
            error=task.get("error"),
            created_at=task["created_at"],
            completed_at=task.get("completed_at"),
        ))

    return TaskListResponse(
        tasks=tasks,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: CurrentUser,
    db: Database,
) -> TaskResponse:
    """Get a specific task by ID."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        task = await db.tasks.find_one({
            "_id": ObjectId(task_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return TaskResponse(
        id=str(task["_id"]),
        company_id=task["company_id"],
        user_id=task["user_id"],
        department=task["department"],
        agent=task["agent"],
        type=task["type"],
        input=task["input"],
        output=task.get("output"),
        status=task["status"],
        error=task.get("error"),
        created_at=task["created_at"],
        completed_at=task.get("completed_at"),
    )


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    current_user: CurrentUser,
    db: Database,
) -> TaskResponse:
    """Retry a failed task."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        task = await db.tasks.find_one({
            "_id": ObjectId(task_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task["status"] not in ["failed", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed or pending tasks can be retried",
        )

    # Reset task status
    now = datetime.utcnow()
    await db.tasks.update_one(
        {"_id": ObjectId(task_id)},
        {
            "$set": {
                "status": "pending",
                "error": None,
                "output": None,
                "updated_at": now,
                "completed_at": None,
            },
            "$inc": {"retry_count": 1}
        }
    )

    # Determine which job to enqueue based on agent
    job_name_map = {
        "instagram_specialist": "process_instagram_task",
        "copywriter": "process_copywriter_task",
        "invoice_worker": "process_invoice_task",
        "cashflow_analyst": "process_cashflow_task",
    }

    job_name = job_name_map.get(task["agent"])
    if job_name:
        try:
            pool = await get_task_queue()
            await pool.enqueue_job(job_name, task_id, task["input"])
        except Exception as e:
            await db.tasks.update_one(
                {"_id": ObjectId(task_id)},
                {"$set": {"error": f"Queue error: {str(e)}"}}
            )

    updated_task = await db.tasks.find_one({"_id": ObjectId(task_id)})

    return TaskResponse(
        id=str(updated_task["_id"]),
        company_id=updated_task["company_id"],
        user_id=updated_task["user_id"],
        department=updated_task["department"],
        agent=updated_task["agent"],
        type=updated_task["type"],
        input=updated_task["input"],
        output=updated_task.get("output"),
        status=updated_task["status"],
        error=updated_task.get("error"),
        created_at=updated_task["created_at"],
        completed_at=updated_task.get("completed_at"),
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: CurrentUser,
    db: Database,
) -> None:
    """Delete a task."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        result = await db.tasks.delete_one({
            "_id": ObjectId(task_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")


# ============================================================================
# FEEDBACK ENDPOINTS
# ============================================================================


@router.post("/{task_id}/feedback", response_model=TaskFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    task_id: str,
    data: TaskFeedbackInput,
    current_user: CurrentUser,
    db: Database,
) -> TaskFeedbackResponse:
    """Submit feedback for a completed task."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Verify task exists and belongs to company
    try:
        task = await db.tasks.find_one({
            "_id": ObjectId(task_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only submit feedback for completed tasks",
        )

    # Check if feedback already exists
    existing = await db.feedbacks.find_one({"task_id": task_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback already submitted for this task",
        )

    now = datetime.utcnow()
    feedback_doc = {
        "task_id": task_id,
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "agent": task["agent"],
        "department": task["department"],
        "rating": data.rating,
        "used": data.used,
        "edited": data.edited,
        "edit_percentage": data.edit_percentage,
        "comments": data.comments,
        "created_at": now,
    }

    result = await db.feedbacks.insert_one(feedback_doc)

    # Update task with feedback reference
    await db.tasks.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"feedback_id": str(result.inserted_id), "has_feedback": True}}
    )

    # Store successful task in memory for learning (rating >= 4)
    if data.rating >= 4 and task.get("output"):
        try:
            await memory_service.store_successful_task(
                company_id=current_user.company_id,
                agent=task["agent"],
                task_input=task["input"],
                task_output=task["output"],
                rating=data.rating,
            )
        except Exception:
            pass  # Memory storage is optional, don't fail the request

    return TaskFeedbackResponse(
        id=str(result.inserted_id),
        task_id=task_id,
        rating=data.rating,
        used=data.used,
        edited=data.edited,
        edit_percentage=data.edit_percentage,
        comments=data.comments,
        created_at=now,
    )


@router.get("/{task_id}/feedback", response_model=TaskFeedbackResponse)
async def get_task_feedback(
    task_id: str,
    current_user: CurrentUser,
    db: Database,
) -> TaskFeedbackResponse:
    """Get feedback for a specific task."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    feedback = await db.feedbacks.find_one({
        "task_id": task_id,
        "company_id": current_user.company_id,
    })

    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    return TaskFeedbackResponse(
        id=str(feedback["_id"]),
        task_id=feedback["task_id"],
        rating=feedback["rating"],
        used=feedback["used"],
        edited=feedback["edited"],
        edit_percentage=feedback.get("edit_percentage"),
        comments=feedback.get("comments"),
        created_at=feedback["created_at"],
    )


@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    current_user: CurrentUser,
    db: Database,
    department: str | None = Query(None),
    agent: str | None = Query(None),
) -> FeedbackStatsResponse:
    """Get aggregated feedback statistics for the company."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Build match query
    match_query: dict = {"company_id": current_user.company_id}
    if department:
        match_query["department"] = department
    if agent:
        match_query["agent"] = agent

    # Aggregation pipeline
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": None,
                "total_feedbacks": {"$sum": 1},
                "sum_rating": {"$sum": "$rating"},
                "used_count": {"$sum": {"$cond": ["$used", 1, 0]}},
                "edited_count": {"$sum": {"$cond": ["$edited", 1, 0]}},
                "edit_percentages": {
                    "$push": {
                        "$cond": [
                            {"$ne": ["$edit_percentage", None]},
                            "$edit_percentage",
                            "$$REMOVE"
                        ]
                    }
                },
                "ratings": {"$push": "$rating"},
            }
        }
    ]

    results = await db.feedbacks.aggregate(pipeline).to_list(1)

    if not results:
        return FeedbackStatsResponse(
            total_feedbacks=0,
            average_rating=0.0,
            usage_rate=0.0,
            edit_rate=0.0,
            average_edit_percentage=None,
            rating_distribution={"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
        )

    stats = results[0]
    total = stats["total_feedbacks"]

    # Calculate rating distribution
    rating_dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for r in stats["ratings"]:
        rating_dist[str(r)] = rating_dist.get(str(r), 0) + 1

    # Calculate average edit percentage
    edit_percs = [p for p in stats.get("edit_percentages", []) if p is not None]
    avg_edit_perc = sum(edit_percs) / len(edit_percs) if edit_percs else None

    return FeedbackStatsResponse(
        total_feedbacks=total,
        average_rating=stats["sum_rating"] / total if total > 0 else 0.0,
        usage_rate=stats["used_count"] / total if total > 0 else 0.0,
        edit_rate=stats["edited_count"] / total if total > 0 else 0.0,
        average_edit_percentage=avg_edit_perc,
        rating_distribution=rating_dist,
    )


@router.get("/feedback/by-agent", response_model=list[AgentFeedbackStats])
async def get_feedback_by_agent(
    current_user: CurrentUser,
    db: Database,
) -> list[AgentFeedbackStats]:
    """Get feedback statistics grouped by agent."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Get task counts per agent
    task_pipeline = [
        {"$match": {"company_id": current_user.company_id, "status": "completed"}},
        {
            "$group": {
                "_id": {"agent": "$agent", "department": "$department"},
                "total_tasks": {"$sum": 1},
            }
        }
    ]
    task_counts = {
        (r["_id"]["agent"], r["_id"]["department"]): r["total_tasks"]
        async for r in db.tasks.aggregate(task_pipeline)
    }

    # Get feedback stats per agent
    feedback_pipeline = [
        {"$match": {"company_id": current_user.company_id}},
        {
            "$group": {
                "_id": {"agent": "$agent", "department": "$department"},
                "total_feedbacks": {"$sum": 1},
                "sum_rating": {"$sum": "$rating"},
                "used_count": {"$sum": {"$cond": ["$used", 1, 0]}},
                "edited_count": {"$sum": {"$cond": ["$edited", 1, 0]}},
            }
        }
    ]

    results = []
    async for stats in db.feedbacks.aggregate(feedback_pipeline):
        agent = stats["_id"]["agent"]
        department = stats["_id"]["department"]
        total_fb = stats["total_feedbacks"]
        total_tasks = task_counts.get((agent, department), total_fb)

        avg_rating = stats["sum_rating"] / total_fb if total_fb > 0 else 0
        usage_rate = stats["used_count"] / total_fb if total_fb > 0 else 0
        edit_rate = stats["edited_count"] / total_fb if total_fb > 0 else 0

        # Satisfaction score: weighted combination
        # Higher rating, higher usage, lower edit rate = better
        satisfaction = (avg_rating / 5 * 0.5) + (usage_rate * 0.3) + ((1 - edit_rate) * 0.2)

        results.append(AgentFeedbackStats(
            agent=agent,
            department=department,
            total_tasks=total_tasks,
            total_feedbacks=total_fb,
            average_rating=avg_rating,
            usage_rate=usage_rate,
            satisfaction_score=satisfaction,
        ))

    return sorted(results, key=lambda x: x.satisfaction_score, reverse=True)

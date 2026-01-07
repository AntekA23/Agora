from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, Database
from app.schemas.task import TaskResponse, TaskListResponse
from app.services.task_queue import get_task_queue

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

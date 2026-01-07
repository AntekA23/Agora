from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, Database
from app.schemas.task import InstagramTaskInput, CopywriterTaskInput, TaskResponse
from app.services.task_queue import get_task_queue

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/marketing/instagram", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_instagram_task(
    data: InstagramTaskInput,
    current_user: CurrentUser,
    db: Database,
) -> TaskResponse:
    """Create Instagram content generation task."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Check if marketing is enabled for company
    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    if "marketing" not in company.get("enabled_agents", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Marketing agents not enabled for this company",
        )

    now = datetime.utcnow()
    task_doc = {
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "department": "marketing",
        "agent": "instagram_specialist",
        "type": "create_post",
        "input": data.model_dump(),
        "output": None,
        "status": "pending",
        "error": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }

    result = await db.tasks.insert_one(task_doc)
    task_id = str(result.inserted_id)

    # Enqueue task for processing
    try:
        pool = await get_task_queue()
        await pool.enqueue_job("process_instagram_task", task_id, data.model_dump())
    except Exception as e:
        # If queue fails, still return task (can retry later)
        await db.tasks.update_one(
            {"_id": result.inserted_id},
            {"$set": {"error": f"Queue error: {str(e)}", "status": "pending"}}
        )

    return TaskResponse(
        id=task_id,
        company_id=current_user.company_id,
        user_id=current_user.id or "",
        department="marketing",
        agent="instagram_specialist",
        type="create_post",
        input=data.model_dump(),
        output=None,
        status="pending",
        error=None,
        created_at=now,
        completed_at=None,
    )


@router.post("/marketing/copywriter", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_copywriter_task(
    data: CopywriterTaskInput,
    current_user: CurrentUser,
    db: Database,
) -> TaskResponse:
    """Create copywriting task."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    if "marketing" not in company.get("enabled_agents", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Marketing agents not enabled for this company",
        )

    now = datetime.utcnow()
    task_doc = {
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "department": "marketing",
        "agent": "copywriter",
        "type": "create_copy",
        "input": data.model_dump(),
        "output": None,
        "status": "pending",
        "error": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }

    result = await db.tasks.insert_one(task_doc)
    task_id = str(result.inserted_id)

    try:
        pool = await get_task_queue()
        await pool.enqueue_job("process_copywriter_task", task_id, data.model_dump())
    except Exception as e:
        await db.tasks.update_one(
            {"_id": result.inserted_id},
            {"$set": {"error": f"Queue error: {str(e)}", "status": "pending"}}
        )

    return TaskResponse(
        id=task_id,
        company_id=current_user.company_id,
        user_id=current_user.id or "",
        department="marketing",
        agent="copywriter",
        type="create_copy",
        input=data.model_dump(),
        output=None,
        status="pending",
        error=None,
        created_at=now,
        completed_at=None,
    )

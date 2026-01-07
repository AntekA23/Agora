from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.schemas.task import InstagramTaskInput, CopywriterTaskInput, TaskResponse
from app.services.task_queue import get_task_queue
from app.services.agents.tools.image_generator import image_service

router = APIRouter(prefix="/agents", tags=["agents"])


# ============================================================================
# IMAGE GENERATION SCHEMAS
# ============================================================================


class ImageGenerateRequest(BaseModel):
    """Request to generate an image."""
    prompt: str = Field(..., min_length=10, description="Opis obrazu do wygenerowania")
    platform: str = Field(default="instagram", description="Platforma: instagram, facebook, linkedin")
    style: str = Field(default="natural", description="Styl: natural, vivid")


class ImageGenerateResponse(BaseModel):
    """Response with generated image."""
    url: str
    revised_prompt: str
    platform: str


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


# ============================================================================
# IMAGE GENERATION ENDPOINT
# ============================================================================


@router.post("/marketing/image", response_model=ImageGenerateResponse)
async def generate_image(
    data: ImageGenerateRequest,
    current_user: CurrentUser,
    db: Database,
) -> ImageGenerateResponse:
    """Generate an image using DALL-E 3.

    This is a synchronous endpoint that returns the image URL directly.
    Use for quick image generation without task queuing.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Verify company exists
    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Get brand style from knowledge base
    knowledge = company.get("knowledge", {})
    brand_guidelines = knowledge.get("brand_guidelines", {})
    brand_style = brand_guidelines.get("tone_of_voice", "")

    try:
        result = await image_service.generate_post_image(
            description=data.prompt,
            brand_style=brand_style,
            platform=data.platform,
        )

        # Log usage for analytics
        await db.image_generations.insert_one({
            "company_id": current_user.company_id,
            "user_id": current_user.id,
            "prompt": data.prompt,
            "platform": data.platform,
            "url": result["url"],
            "created_at": datetime.utcnow(),
        })

        return ImageGenerateResponse(
            url=result["url"],
            revised_prompt=result["revised_prompt"],
            platform=data.platform,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {e!s}",
        )

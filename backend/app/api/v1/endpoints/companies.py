from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, Database
from app.schemas import CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=CompanyResponse)
async def get_my_company(current_user: CurrentUser, db: Database) -> CompanyResponse:
    """Get current user's company."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no company",
        )

    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return CompanyResponse(
        id=str(company["_id"]),
        name=company["name"],
        slug=company["slug"],
        industry=company["industry"],
        size=company["size"],
        settings=company["settings"],
        enabled_agents=company["enabled_agents"],
        subscription_plan=company["subscription"]["plan"],
        subscription_valid_until=company["subscription"].get("valid_until"),
        created_at=company["created_at"],
    )


@router.patch("/me", response_model=CompanyResponse)
async def update_my_company(
    data: CompanyUpdate,
    current_user: CurrentUser,
    db: Database,
) -> CompanyResponse:
    """Update current user's company (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update company settings",
        )

    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no company",
        )

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    update_data["updated_at"] = datetime.utcnow()

    result = await db.companies.find_one_and_update(
        {"_id": ObjectId(current_user.company_id)},
        {"$set": update_data},
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return CompanyResponse(
        id=str(result["_id"]),
        name=result["name"],
        slug=result["slug"],
        industry=result["industry"],
        size=result["size"],
        settings=result["settings"],
        enabled_agents=result["enabled_agents"],
        subscription_plan=result["subscription"]["plan"],
        subscription_valid_until=result["subscription"].get("valid_until"),
        created_at=result["created_at"],
    )

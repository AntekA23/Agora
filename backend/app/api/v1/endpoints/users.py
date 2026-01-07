from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, Database
from app.core.security import hash_password, verify_password
from app.schemas import ChangePasswordRequest, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """Get current user profile."""
    return UserResponse(
        id=current_user.id or "",
        email=current_user.email,
        name=current_user.name,
        company_id=current_user.company_id,
        role=current_user.role,
        preferences=current_user.preferences,
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: CurrentUser,
    db: Database,
) -> UserResponse:
    """Update current user profile."""
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    update_data["updated_at"] = datetime.utcnow()

    if "preferences" in update_data:
        update_data["preferences"] = update_data["preferences"].model_dump()

    await db.users.update_one(
        {"_id": current_user.id},
        {"$set": update_data},
    )

    updated_user = await db.users.find_one({"_id": current_user.id})
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=str(updated_user["_id"]),
        email=updated_user["email"],
        name=updated_user["name"],
        company_id=updated_user.get("company_id"),
        role=updated_user["role"],
        preferences=updated_user["preferences"],
    )


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Database,
) -> None:
    """Change current user password."""
    user = await db.users.find_one({"_id": current_user.id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    await db.users.update_one(
        {"_id": current_user.id},
        {
            "$set": {
                "password_hash": hash_password(data.new_password),
                "updated_at": datetime.utcnow(),
            }
        },
    )

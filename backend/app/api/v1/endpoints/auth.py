import re
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import CurrentUser, Database
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: Database) -> TokenResponse:
    """Register a new user and company."""
    print(f"[REGISTER] Attempting to register: email={data.email}, company={data.company_name}")

    existing_user = await db.users.find_one({"email": data.email})
    print(f"[REGISTER] Existing user check: {existing_user is not None}")
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    company_slug = slugify(data.company_name)
    print(f"[REGISTER] Company slug: '{data.company_name}' -> '{company_slug}'")

    existing_company = await db.companies.find_one({"slug": company_slug})
    print(f"[REGISTER] Existing company check: {existing_company}")
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name already taken",
        )

    now = datetime.utcnow()
    company_doc = {
        "name": data.company_name,
        "slug": company_slug,
        "industry": "",
        "size": "small",
        "settings": {
            "brand_voice": "profesjonalny",
            "target_audience": "",
            "language": "pl",
        },
        "enabled_agents": ["marketing"],
        "subscription": {"plan": "free", "valid_until": None},
        "created_at": now,
        "updated_at": now,
    }
    company_result = await db.companies.insert_one(company_doc)
    company_id = str(company_result.inserted_id)

    user_doc = {
        "email": data.email,
        "password_hash": hash_password(data.password),
        "name": data.name,
        "company_id": company_id,
        "role": "admin",
        "preferences": {"theme": "dark", "language": "pl"},
        "created_at": now,
        "updated_at": now,
    }
    user_result = await db.users.insert_one(user_doc)
    user_id = str(user_result.inserted_id)

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Database) -> TokenResponse:
    """Authenticate user and return tokens."""
    user = await db.users.find_one({"email": data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_id = str(user["_id"])
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(data: RefreshTokenRequest, db: Database) -> TokenResponse:
    """Refresh access token using refresh token."""
    payload = decode_token(data.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser) -> UserResponse:
    """Get current user information."""
    return UserResponse(
        id=current_user.id or "",
        email=current_user.email,
        name=current_user.name,
        company_id=current_user.company_id,
        role=current_user.role,
        preferences=current_user.preferences,
    )

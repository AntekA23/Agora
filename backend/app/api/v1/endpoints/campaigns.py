"""Multi-Agent Campaign API endpoints."""

from datetime import datetime
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.agents.campaigns import campaign_service, CampaignType

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


# ============================================================================
# SCHEMAS
# ============================================================================


class SocialMediaCampaignRequest(BaseModel):
    """Request for social media campaign."""
    brief: str = Field(..., min_length=10, description="Opis kampanii")
    platforms: list[str] = Field(default=["instagram"], description="Platformy docelowe")
    include_image: bool = Field(default=True, description="Czy generować obraz")


class FullMarketingCampaignRequest(BaseModel):
    """Request for full marketing campaign."""
    brief: str = Field(..., min_length=10, description="Główny brief kampanii")
    campaign_name: str = Field(default="", description="Nazwa kampanii")
    copy_types: list[str] = Field(default=["ad", "slogan"], description="Typy tekstów")
    platforms: list[str] = Field(default=["instagram", "facebook"], description="Platformy")


class ProductLaunchRequest(BaseModel):
    """Request for product launch campaign."""
    product_name: str = Field(..., min_length=2, description="Nazwa produktu")
    product_description: str = Field(..., min_length=10, description="Opis produktu")
    key_features: list[str] = Field(default_factory=list, description="Kluczowe cechy")
    price: str = Field(default="", description="Cena produktu")


class PromoCampaignRequest(BaseModel):
    """Request for promotional campaign."""
    promo_type: str = Field(..., description="Typ promocji: discount, sale, event, seasonal")
    promo_details: str = Field(..., min_length=10, description="Szczegóły promocji")
    valid_until: str = Field(default="", description="Data ważności promocji")


class CampaignResponse(BaseModel):
    """Campaign response."""
    id: str
    campaign_type: str
    campaign_name: str | None = None
    brief: str
    created_at: str
    outputs: dict[str, Any]
    agents_used: list[str]
    summary: dict[str, Any] | None = None


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/social-media", response_model=CampaignResponse)
async def create_social_media_campaign(
    data: SocialMediaCampaignRequest,
    current_user: CurrentUser,
    db: Database,
) -> CampaignResponse:
    """Create a social media campaign with post and image.

    Orchestrates Instagram Specialist and Image Generator to create
    a complete social media post package.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Get company settings
    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    settings = company.get("settings", {})

    # Create campaign
    result = await campaign_service.create_social_media_campaign(
        company_id=current_user.company_id,
        brief=data.brief,
        platforms=data.platforms,
        brand_voice=settings.get("brand_voice", "profesjonalny"),
        target_audience=settings.get("target_audience", ""),
        include_image=data.include_image,
    )

    # Store campaign in database
    campaign_doc = {
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "campaign_type": result["campaign_type"],
        "brief": result["brief"],
        "outputs": result["outputs"],
        "agents_used": result["agents_used"],
        "created_at": datetime.utcnow(),
    }
    inserted = await db.campaigns.insert_one(campaign_doc)

    return CampaignResponse(
        id=str(inserted.inserted_id),
        campaign_type=result["campaign_type"],
        brief=result["brief"],
        created_at=result["created_at"],
        outputs=result["outputs"],
        agents_used=result["agents_used"],
    )


@router.post("/full-marketing", response_model=CampaignResponse)
async def create_full_marketing_campaign(
    data: FullMarketingCampaignRequest,
    current_user: CurrentUser,
    db: Database,
) -> CampaignResponse:
    """Create a full marketing campaign package.

    Orchestrates Copywriter, Instagram Specialist, and Image Generator
    to create a complete marketing package with:
    - Multiple copy variants (ads, slogans, etc.)
    - Social media posts for multiple platforms
    - Custom images for each platform
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    settings = company.get("settings", {})

    result = await campaign_service.create_full_marketing_campaign(
        company_id=current_user.company_id,
        brief=data.brief,
        campaign_name=data.campaign_name,
        brand_voice=settings.get("brand_voice", "profesjonalny"),
        target_audience=settings.get("target_audience", ""),
        copy_types=data.copy_types,
        platforms=data.platforms,
    )

    campaign_doc = {
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "campaign_type": result["campaign_type"],
        "campaign_name": result["campaign_name"],
        "brief": result["brief"],
        "outputs": result["outputs"],
        "agents_used": result["agents_used"],
        "summary": result["summary"],
        "created_at": datetime.utcnow(),
    }
    inserted = await db.campaigns.insert_one(campaign_doc)

    return CampaignResponse(
        id=str(inserted.inserted_id),
        campaign_type=result["campaign_type"],
        campaign_name=result["campaign_name"],
        brief=result["brief"],
        created_at=result["created_at"],
        outputs=result["outputs"],
        agents_used=result["agents_used"],
        summary=result["summary"],
    )


@router.post("/product-launch", response_model=CampaignResponse)
async def create_product_launch_campaign(
    data: ProductLaunchRequest,
    current_user: CurrentUser,
    db: Database,
) -> CampaignResponse:
    """Create a product launch campaign.

    Specialized campaign for launching new products with:
    - Product description
    - Ad copy and slogans
    - Social media posts
    - Product visuals
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    settings = company.get("settings", {})

    result = await campaign_service.create_product_launch_campaign(
        company_id=current_user.company_id,
        product_name=data.product_name,
        product_description=data.product_description,
        key_features=data.key_features,
        brand_voice=settings.get("brand_voice", "profesjonalny"),
        target_audience=settings.get("target_audience", ""),
        price=data.price,
    )

    campaign_doc = {
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "campaign_type": result["campaign_type"],
        "campaign_name": result["campaign_name"],
        "brief": result["brief"],
        "outputs": result["outputs"],
        "agents_used": result["agents_used"],
        "summary": result["summary"],
        "created_at": datetime.utcnow(),
    }
    inserted = await db.campaigns.insert_one(campaign_doc)

    return CampaignResponse(
        id=str(inserted.inserted_id),
        campaign_type=result["campaign_type"],
        campaign_name=result["campaign_name"],
        brief=result["brief"],
        created_at=result["created_at"],
        outputs=result["outputs"],
        agents_used=result["agents_used"],
        summary=result["summary"],
    )


@router.post("/promo", response_model=CampaignResponse)
async def create_promo_campaign(
    data: PromoCampaignRequest,
    current_user: CurrentUser,
    db: Database,
) -> CampaignResponse:
    """Create a promotional campaign.

    Specialized for time-limited promotions with urgency messaging:
    - Discount campaigns
    - Sales events
    - Seasonal offers
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    settings = company.get("settings", {})

    result = await campaign_service.create_promo_campaign(
        company_id=current_user.company_id,
        promo_type=data.promo_type,
        promo_details=data.promo_details,
        valid_until=data.valid_until,
        brand_voice=settings.get("brand_voice", "profesjonalny"),
        target_audience=settings.get("target_audience", ""),
    )

    campaign_doc = {
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "campaign_type": CampaignType.PROMO_CAMPAIGN,
        "brief": result["brief"],
        "outputs": result["outputs"],
        "agents_used": result["agents_used"],
        "created_at": datetime.utcnow(),
    }
    inserted = await db.campaigns.insert_one(campaign_doc)

    return CampaignResponse(
        id=str(inserted.inserted_id),
        campaign_type=CampaignType.PROMO_CAMPAIGN,
        brief=result["brief"],
        created_at=result["created_at"],
        outputs=result["outputs"],
        agents_used=result["agents_used"],
    )


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    current_user: CurrentUser,
    db: Database,
) -> list[CampaignResponse]:
    """List all campaigns for the current company."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    campaigns = []
    async for doc in db.campaigns.find(
        {"company_id": current_user.company_id}
    ).sort("created_at", -1).limit(50):
        campaigns.append(CampaignResponse(
            id=str(doc["_id"]),
            campaign_type=doc["campaign_type"],
            campaign_name=doc.get("campaign_name"),
            brief=doc["brief"],
            created_at=doc["created_at"].isoformat(),
            outputs=doc["outputs"],
            agents_used=doc["agents_used"],
            summary=doc.get("summary"),
        ))

    return campaigns


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: CurrentUser,
    db: Database,
) -> CampaignResponse:
    """Get a specific campaign by ID."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        doc = await db.campaigns.find_one({
            "_id": ObjectId(campaign_id),
            "company_id": current_user.company_id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    return CampaignResponse(
        id=str(doc["_id"]),
        campaign_type=doc["campaign_type"],
        campaign_name=doc.get("campaign_name"),
        brief=doc["brief"],
        created_at=doc["created_at"].isoformat(),
        outputs=doc["outputs"],
        agents_used=doc["agents_used"],
        summary=doc.get("summary"),
    )

"""Onboarding API - Smart Setup with website auto-extraction.

This endpoint provides intelligent onboarding that can automatically
extract company information from websites.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

from app.api.deps import CurrentUser, Database
from app.services.website_analyzer import website_analyzer, ExtractedBrandInfo

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================


class AnalyzeWebsiteRequest(BaseModel):
    """Request to analyze a company website."""

    url: Optional[str] = Field(
        default=None,
        description="URL strony firmowej do analizy",
        examples=["www.example.com", "https://example.com"],
    )
    company_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Nazwa firmy (jesli znana)",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Krotki opis firmy (jesli znany)",
    )


class ExtractedInfoResponse(BaseModel):
    """Response with extracted brand information."""

    company_name: str
    industry: str
    description: str
    target_audience: str
    brand_voice: str
    products_services: list[str]
    unique_selling_points: list[str]
    suggested_hashtags: list[str]
    confidence_score: float = Field(ge=0, le=1)
    source: str = Field(
        description="Zrodlo danych: 'website', 'ai_suggestion', 'empty'"
    )


class SmartSetupRequest(BaseModel):
    """Request to complete smart setup."""

    company_name: str = Field(..., min_length=2, max_length=200)
    description: str = Field(default="", max_length=1000)
    website_url: Optional[str] = Field(default=None)
    industry: str = Field(default="", max_length=100)
    target_audience: str = Field(default="", max_length=500)
    brand_voice: str = Field(default="profesjonalny", max_length=200)
    skip_analysis: bool = Field(
        default=False,
        description="Pomin analize i uzyj podanych danych",
    )


class SmartSetupResponse(BaseModel):
    """Response from smart setup completion."""

    success: bool
    message: str
    extracted_info: Optional[ExtractedInfoResponse] = None
    company_updated: bool = False


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "/analyze",
    response_model=ExtractedInfoResponse,
    summary="Analizuj strone firmowa",
    description="Analizuje strone www firmy i wyodrebnia informacje o marce.",
)
async def analyze_website(
    data: AnalyzeWebsiteRequest,
    current_user: CurrentUser,
) -> ExtractedInfoResponse:
    """Analyze a company website and extract brand information.

    This endpoint:
    1. Fetches content from the provided URL using Tavily
    2. Uses AI to extract brand-relevant information
    3. Returns structured data for the onboarding form

    Can also work without URL - will generate suggestions based on
    company name and description if provided.
    """
    if not data.url and not data.company_name and not data.description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Podaj URL, nazwe firmy lub opis",
        )

    # Run analysis
    result = await website_analyzer.analyze(
        url=data.url,
        company_name=data.company_name,
        description=data.description,
    )

    # Determine source
    if data.url and result.confidence_score > 0.3:
        source = "website"
    elif result.confidence_score > 0.2:
        source = "ai_suggestion"
    else:
        source = "empty"

    return ExtractedInfoResponse(
        company_name=result.company_name,
        industry=result.industry,
        description=result.description,
        target_audience=result.target_audience,
        brand_voice=result.brand_voice,
        products_services=result.products_services,
        unique_selling_points=result.unique_selling_points,
        suggested_hashtags=result.suggested_hashtags,
        confidence_score=result.confidence_score,
        source=source,
    )


@router.post(
    "/complete",
    response_model=SmartSetupResponse,
    summary="Zakoncz Smart Setup",
    description="Zapisuje dane z onboardingu i opcjonalnie analizuje strone.",
)
async def complete_smart_setup(
    data: SmartSetupRequest,
    current_user: CurrentUser,
    db: Database,
) -> SmartSetupResponse:
    """Complete the smart setup process.

    This endpoint:
    1. Optionally analyzes the website if URL provided
    2. Saves company information to the database
    3. Returns the final extracted/merged data
    """
    from bson import ObjectId

    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    extracted_info = None

    # Analyze website if URL provided and not skipping
    if data.website_url and not data.skip_analysis:
        result = await website_analyzer.analyze(
            url=data.website_url,
            company_name=data.company_name,
            description=data.description,
        )

        # Determine source
        if result.confidence_score > 0.3:
            source = "website"
        elif result.confidence_score > 0.2:
            source = "ai_suggestion"
        else:
            source = "empty"

        extracted_info = ExtractedInfoResponse(
            company_name=result.company_name or data.company_name,
            industry=result.industry or data.industry,
            description=result.description or data.description,
            target_audience=result.target_audience or data.target_audience,
            brand_voice=result.brand_voice or data.brand_voice,
            products_services=result.products_services,
            unique_selling_points=result.unique_selling_points,
            suggested_hashtags=result.suggested_hashtags,
            confidence_score=result.confidence_score,
            source=source,
        )

        # Use extracted data if better
        final_industry = result.industry or data.industry
        final_target = result.target_audience or data.target_audience
        final_voice = result.brand_voice or data.brand_voice
    else:
        final_industry = data.industry
        final_target = data.target_audience
        final_voice = data.brand_voice

    # Update company in database
    try:
        update_data = {
            "name": data.company_name,
            "industry": final_industry,
            "settings.brand_voice": final_voice,
            "settings.target_audience": final_target,
            "settings.language": "pl",
            "onboarding_completed": True,
        }

        if data.website_url:
            update_data["website"] = data.website_url

        await db.companies.update_one(
            {"_id": ObjectId(current_user.company_id)},
            {"$set": update_data},
        )

        return SmartSetupResponse(
            success=True,
            message="Onboarding zakonczony pomyslnie!",
            extracted_info=extracted_info,
            company_updated=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Blad zapisu: {str(e)}",
        )


@router.get(
    "/status",
    summary="Status onboardingu",
    description="Sprawdza czy uzytkownik ukonczyl onboarding.",
)
async def get_onboarding_status(
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Check if user has completed onboarding."""
    from bson import ObjectId

    if not current_user.company_id:
        return {"completed": False, "reason": "no_company"}

    company = await db.companies.find_one(
        {"_id": ObjectId(current_user.company_id)}
    )

    if not company:
        return {"completed": False, "reason": "company_not_found"}

    # Check if basic setup is done
    has_industry = bool(company.get("industry"))
    has_settings = bool(company.get("settings", {}).get("brand_voice"))
    onboarding_flag = company.get("onboarding_completed", False)

    return {
        "completed": onboarding_flag or (has_industry and has_settings),
        "has_industry": has_industry,
        "has_brand_settings": has_settings,
        "company_name": company.get("name", ""),
    }

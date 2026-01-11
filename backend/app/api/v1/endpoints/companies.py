from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, Database
from app.schemas import CompanyResponse, CompanyUpdate
from app.schemas.company import (
    KnowledgeResponse,
    KnowledgeUpdate,
    ProductInput,
    ServiceInput,
    CompetitorInput,
    BrandGuidelinesInput,
    WebsiteAnalyzeRequest,
    WebsiteAnalyzeResponse,
    BrandWizardComplete,
)
from app.models.company import (
    CompanyKnowledge,
    Product,
    Service,
    Competitor,
    BrandIdentity,
    TargetAudience,
    CommunicationStyle,
    ContentPreferences,
)
from app.core.config import settings

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


# ============================================================================
# KNOWLEDGE BASE ENDPOINTS
# ============================================================================


@router.get("/me/knowledge", response_model=KnowledgeResponse)
async def get_company_knowledge(
    current_user: CurrentUser,
    db: Database,
) -> KnowledgeResponse:
    """Get company knowledge base."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no company")

    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    knowledge_data = company.get("knowledge", {})
    knowledge = CompanyKnowledge(**knowledge_data) if knowledge_data else CompanyKnowledge()

    return KnowledgeResponse(knowledge=knowledge)


@router.patch("/me/knowledge", response_model=KnowledgeResponse)
async def update_company_knowledge(
    data: KnowledgeUpdate,
    current_user: CurrentUser,
    db: Database,
) -> KnowledgeResponse:
    """Update company knowledge base (partial update)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update knowledge base")

    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no company")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    # Build update with knowledge prefix
    knowledge_update = {f"knowledge.{k}": v for k, v in update_data.items()}
    knowledge_update["updated_at"] = datetime.utcnow()

    result = await db.companies.find_one_and_update(
        {"_id": ObjectId(current_user.company_id)},
        {"$set": knowledge_update},
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    knowledge_data = result.get("knowledge", {})
    knowledge = CompanyKnowledge(**knowledge_data) if knowledge_data else CompanyKnowledge()

    return KnowledgeResponse(knowledge=knowledge)


# --- Products ---

@router.post("/me/knowledge/products", response_model=KnowledgeResponse)
async def add_product(
    data: ProductInput,
    current_user: CurrentUser,
    db: Database,
) -> KnowledgeResponse:
    """Add a product to company knowledge base."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can modify knowledge base")

    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no company")

    product = Product(**data.model_dump())

    result = await db.companies.find_one_and_update(
        {"_id": ObjectId(current_user.company_id)},
        {
            "$push": {"knowledge.products": product.model_dump()},
            "$set": {"updated_at": datetime.utcnow()},
        },
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    knowledge = CompanyKnowledge(**result.get("knowledge", {}))
    return KnowledgeResponse(knowledge=knowledge)


@router.delete("/me/knowledge/products/{product_name}", response_model=KnowledgeResponse)
async def remove_product(
    product_name: str,
    current_user: CurrentUser,
    db: Database,
) -> KnowledgeResponse:
    """Remove a product from company knowledge base."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can modify knowledge base")

    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no company")

    result = await db.companies.find_one_and_update(
        {"_id": ObjectId(current_user.company_id)},
        {
            "$pull": {"knowledge.products": {"name": product_name}},
            "$set": {"updated_at": datetime.utcnow()},
        },
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    knowledge = CompanyKnowledge(**result.get("knowledge", {}))
    return KnowledgeResponse(knowledge=knowledge)


# --- Services ---

@router.post("/me/knowledge/services", response_model=KnowledgeResponse)
async def add_service(
    data: ServiceInput,
    current_user: CurrentUser,
    db: Database,
) -> KnowledgeResponse:
    """Add a service to company knowledge base."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can modify knowledge base")

    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no company")

    service = Service(**data.model_dump())

    result = await db.companies.find_one_and_update(
        {"_id": ObjectId(current_user.company_id)},
        {
            "$push": {"knowledge.services": service.model_dump()},
            "$set": {"updated_at": datetime.utcnow()},
        },
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    knowledge = CompanyKnowledge(**result.get("knowledge", {}))
    return KnowledgeResponse(knowledge=knowledge)


@router.delete("/me/knowledge/services/{service_name}", response_model=KnowledgeResponse)
async def remove_service(
    service_name: str,
    current_user: CurrentUser,
    db: Database,
) -> KnowledgeResponse:
    """Remove a service from company knowledge base."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can modify knowledge base")

    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no company")

    result = await db.companies.find_one_and_update(
        {"_id": ObjectId(current_user.company_id)},
        {
            "$pull": {"knowledge.services": {"name": service_name}},
            "$set": {"updated_at": datetime.utcnow()},
        },
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    knowledge = CompanyKnowledge(**result.get("knowledge", {}))
    return KnowledgeResponse(knowledge=knowledge)


# --- Competitors ---

@router.post("/me/knowledge/competitors", response_model=KnowledgeResponse)
async def add_competitor(
    data: CompetitorInput,
    current_user: CurrentUser,
    db: Database,
) -> KnowledgeResponse:
    """Add a competitor to company knowledge base."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can modify knowledge base")

    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no company")

    competitor = Competitor(**data.model_dump())

    result = await db.companies.find_one_and_update(
        {"_id": ObjectId(current_user.company_id)},
        {
            "$push": {"knowledge.competitors": competitor.model_dump()},
            "$set": {"updated_at": datetime.utcnow()},
        },
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    knowledge = CompanyKnowledge(**result.get("knowledge", {}))
    return KnowledgeResponse(knowledge=knowledge)


@router.delete("/me/knowledge/competitors/{competitor_name}", response_model=KnowledgeResponse)
async def remove_competitor(
    competitor_name: str,
    current_user: CurrentUser,
    db: Database,
) -> KnowledgeResponse:
    """Remove a competitor from company knowledge base."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can modify knowledge base")

    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no company")

    result = await db.companies.find_one_and_update(
        {"_id": ObjectId(current_user.company_id)},
        {
            "$pull": {"knowledge.competitors": {"name": competitor_name}},
            "$set": {"updated_at": datetime.utcnow()},
        },
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    knowledge = CompanyKnowledge(**result.get("knowledge", {}))
    return KnowledgeResponse(knowledge=knowledge)


# --- Brand Guidelines ---

@router.put("/me/knowledge/brand-guidelines", response_model=KnowledgeResponse)
async def update_brand_guidelines(
    data: BrandGuidelinesInput,
    current_user: CurrentUser,
    db: Database,
) -> KnowledgeResponse:
    """Update brand guidelines."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can modify knowledge base")

    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no company")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    # Build update with nested path
    guidelines_update = {f"knowledge.brand_guidelines.{k}": v for k, v in update_data.items()}
    guidelines_update["updated_at"] = datetime.utcnow()

    result = await db.companies.find_one_and_update(
        {"_id": ObjectId(current_user.company_id)},
        {"$set": guidelines_update},
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    knowledge = CompanyKnowledge(**result.get("knowledge", {}))
    return KnowledgeResponse(knowledge=knowledge)


# ============================================================================
# BRAND WIZARD ENDPOINTS
# ============================================================================


@router.post("/me/wizard/analyze-website", response_model=WebsiteAnalyzeResponse)
async def analyze_website(
    data: WebsiteAnalyzeRequest,
    current_user: CurrentUser,
) -> WebsiteAnalyzeResponse:
    """Analyze company website using Tavily to extract information.

    This helps pre-fill the brand wizard with information from the website.
    """
    if not settings.TAVILY_API_KEY:
        return WebsiteAnalyzeResponse(
            success=False,
            error="Tavily API key not configured. Please fill the wizard manually.",
        )

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.TAVILY_API_KEY)

        # Search for company info
        url = data.url
        if not url.startswith("http"):
            url = f"https://{url}"

        # Get website content
        search_result = client.search(
            query=f"site:{url} company about us products services",
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )

        # Extract relevant information using another search
        company_info = client.search(
            query=f"{url} company description mission values target audience",
            search_depth="advanced",
            max_results=3,
            include_answer=True,
        )

        # Process results
        extracted_data = {
            "website": url,
            "raw_content": [],
            "suggested_description": "",
            "suggested_values": [],
            "suggested_products": [],
        }

        # Get the AI-generated answer if available
        if search_result.get("answer"):
            extracted_data["suggested_description"] = search_result["answer"][:500]

        if company_info.get("answer"):
            extracted_data["company_info"] = company_info["answer"][:500]

        # Collect content snippets
        for result in search_result.get("results", [])[:3]:
            content = result.get("content", "")
            if content:
                extracted_data["raw_content"].append({
                    "title": result.get("title", ""),
                    "content": content[:300],
                    "url": result.get("url", ""),
                })

        return WebsiteAnalyzeResponse(
            success=True,
            data=extracted_data,
        )

    except Exception as e:
        return WebsiteAnalyzeResponse(
            success=False,
            error=f"Failed to analyze website: {str(e)}",
        )


@router.post("/me/wizard/complete", response_model=KnowledgeResponse)
async def complete_brand_wizard(
    data: BrandWizardComplete,
    current_user: CurrentUser,
    db: Database,
) -> KnowledgeResponse:
    """Save complete brand wizard data to company knowledge base.

    This endpoint takes all wizard steps and updates the company's
    knowledge base with the provided information.
    """
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

    # Build the knowledge update from wizard data
    knowledge_update = {}

    # Step 1: Basic info
    if data.step1:
        knowledge_update["knowledge.company_description"] = data.step1.company_description
        knowledge_update["knowledge.founded_year"] = data.step1.founded_year
        knowledge_update["knowledge.location"] = data.step1.location
        knowledge_update["knowledge.website"] = data.step1.website

    # Step 2: Brand identity
    if data.step2:
        brand_identity = BrandIdentity(
            mission=data.step2.mission,
            vision=data.step2.vision,
            values=data.step2.values,
            personality_traits=data.step2.personality_traits,
            unique_value_proposition=data.step2.unique_value_proposition,
        )
        knowledge_update["knowledge.brand_identity"] = brand_identity.model_dump()
        # Also update legacy fields for compatibility
        knowledge_update["knowledge.mission"] = data.step2.mission
        knowledge_update["knowledge.vision"] = data.step2.vision
        knowledge_update["knowledge.unique_value_proposition"] = data.step2.unique_value_proposition

    # Step 3: Target audience
    if data.step3:
        target_audience = TargetAudience(
            description=data.step3.description,
            age_from=data.step3.age_from,
            age_to=data.step3.age_to,
            gender=data.step3.gender,
            locations=data.step3.locations,
            interests=data.step3.interests,
            pain_points=data.step3.pain_points,
            goals=data.step3.goals,
            where_they_are=data.step3.where_they_are,
        )
        knowledge_update["knowledge.target_audience"] = target_audience.model_dump()
        # Update legacy settings.target_audience
        knowledge_update["settings.target_audience"] = data.step3.description

    # Step 4: Products and services
    if data.step4:
        products = [Product(**p.model_dump()) for p in data.step4.products]
        services = [Service(**s.model_dump()) for s in data.step4.services]
        knowledge_update["knowledge.products"] = [p.model_dump() for p in products]
        knowledge_update["knowledge.services"] = [s.model_dump() for s in services]
        knowledge_update["knowledge.price_positioning"] = data.step4.price_positioning

    # Step 5: Competition
    if data.step5:
        competitors = [Competitor(**c.model_dump()) for c in data.step5.competitors]
        knowledge_update["knowledge.competitors"] = [c.model_dump() for c in competitors]
        knowledge_update["knowledge.market_position"] = data.step5.market_position

    # Step 6: Communication style
    if data.step6:
        comm_style = CommunicationStyle(
            formality_level=data.step6.formality_level,
            emoji_usage=data.step6.emoji_usage,
            words_to_use=data.step6.words_to_use,
            words_to_avoid=data.step6.words_to_avoid,
            example_phrases=data.step6.example_phrases,
        )
        knowledge_update["knowledge.communication_style"] = comm_style.model_dump()
        # Update legacy brand_guidelines
        knowledge_update["knowledge.brand_guidelines.words_to_use"] = data.step6.words_to_use
        knowledge_update["knowledge.brand_guidelines.words_to_avoid"] = data.step6.words_to_avoid

        # Map formality to brand_voice
        formality_map = {
            1: "bardzo formalny",
            2: "formalny",
            3: "profesjonalny",
            4: "swobodny",
            5: "bardzo swobodny",
        }
        knowledge_update["settings.brand_voice"] = formality_map.get(data.step6.formality_level, "profesjonalny")

    # Step 7: Content preferences
    if data.step7:
        content_prefs = ContentPreferences(
            themes=data.step7.themes,
            hashtag_style=data.step7.hashtag_style,
            branded_hashtags=data.step7.branded_hashtags,
            post_frequency=data.step7.post_frequency,
            preferred_formats=data.step7.preferred_formats,
            content_goals=data.step7.content_goals,
        )
        knowledge_update["knowledge.content_preferences"] = content_prefs.model_dump()
        # Update legacy brand_guidelines
        knowledge_update["knowledge.brand_guidelines.hashtags_always"] = data.step7.branded_hashtags

    # Mark wizard as completed
    knowledge_update["settings.wizard_completed"] = True
    knowledge_update["updated_at"] = datetime.utcnow()

    result = await db.companies.find_one_and_update(
        {"_id": ObjectId(current_user.company_id)},
        {"$set": knowledge_update},
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    knowledge = CompanyKnowledge(**result.get("knowledge", {}))
    return KnowledgeResponse(knowledge=knowledge)


@router.get("/me/wizard/status")
async def get_wizard_status(
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Check if brand wizard has been completed and if reminder should be shown."""
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

    settings_data = company.get("settings", {})
    knowledge_data = company.get("knowledge", {})

    # Check if reminder should be shown
    wizard_completed = settings_data.get("wizard_completed", False)
    reminder_dismissed = settings_data.get("wizard_reminder_dismissed_at") is not None
    snooze_until = settings_data.get("wizard_reminder_snooze_until")
    is_snoozed = snooze_until and datetime.fromisoformat(str(snooze_until)) > datetime.utcnow() if snooze_until else False

    show_reminder = not wizard_completed and not reminder_dismissed and not is_snoozed

    return {
        "wizard_completed": wizard_completed,
        "has_description": bool(knowledge_data.get("company_description")),
        "has_products": bool(knowledge_data.get("products")),
        "has_target_audience": bool(knowledge_data.get("target_audience", {}).get("description")),
        "show_reminder": show_reminder,
        "reminder_dismissed": reminder_dismissed,
        "snooze_until": snooze_until,
    }


from datetime import timedelta
from pydantic import BaseModel
from typing import Literal


class WizardReminderRequest(BaseModel):
    """Request to update wizard reminder preferences."""
    action: Literal["dismiss", "snooze"]
    snooze_days: int = 7


@router.post("/me/wizard/reminder")
async def update_wizard_reminder(
    data: WizardReminderRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Update wizard reminder preferences (dismiss or snooze)."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no company",
        )

    update_data: dict = {"updated_at": datetime.utcnow()}

    if data.action == "dismiss":
        update_data["settings.wizard_reminder_dismissed_at"] = datetime.utcnow()
    elif data.action == "snooze":
        snooze_until = datetime.utcnow() + timedelta(days=data.snooze_days)
        update_data["settings.wizard_reminder_snooze_until"] = snooze_until

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

    return {"success": True, "action": data.action}

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
)
from app.models.company import CompanyKnowledge, Product, Service, Competitor

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

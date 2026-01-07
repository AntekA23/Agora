"""Legal Department API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.agents.legal import (
    review_contract,
    compare_contracts,
    check_gdpr_compliance,
    generate_privacy_policy,
    generate_data_processing_agreement,
    generate_terms_of_service,
    generate_return_policy,
)

router = APIRouter(prefix="/legal", tags=["legal"])


# ============================================================================
# SCHEMAS
# ============================================================================


class ContractReviewRequest(BaseModel):
    """Request for contract review."""
    contract_text: str = Field(..., min_length=100)
    contract_type: str = "general"
    your_role: str = "buyer"
    key_concerns: list[str] | None = None
    industry: str = ""


class ContractCompareRequest(BaseModel):
    """Request for contract comparison."""
    contract_a: str = Field(..., min_length=100)
    contract_b: str = Field(..., min_length=100)
    contract_type: str = "general"


class GDPRCheckRequest(BaseModel):
    """Request for GDPR compliance check."""
    business_description: str = Field(..., min_length=20)
    data_collected: list[str] = Field(..., min_length=1)
    data_processing_purposes: list[str] = Field(..., min_length=1)
    third_party_sharing: list[str] | None = None
    has_privacy_policy: bool = False
    has_consent_mechanism: bool = False
    stores_data_outside_eu: bool = False


class PrivacyPolicyRequest(BaseModel):
    """Request for privacy policy generation."""
    company_address: str = Field(..., min_length=10)
    business_type: str = Field(..., min_length=3)
    data_collected: list[str] = Field(..., min_length=1)
    data_purposes: list[str] = Field(..., min_length=1)
    third_parties: list[str] | None = None
    cookies_used: bool = True
    analytics_tools: list[str] | None = None
    contact_email: str = ""
    iod_contact: str = ""


class DPARequest(BaseModel):
    """Request for Data Processing Agreement."""
    controller_name: str = Field(..., min_length=2)
    controller_address: str = Field(..., min_length=10)
    processor_name: str = Field(..., min_length=2)
    processor_address: str = Field(..., min_length=10)
    processing_subject: str = Field(..., min_length=10)
    data_categories: list[str] = Field(..., min_length=1)
    data_subjects: list[str] = Field(..., min_length=1)
    processing_duration: str = ""


class TermsOfServiceRequest(BaseModel):
    """Request for Terms of Service generation."""
    company_address: str = Field(..., min_length=10)
    service_type: str = Field(..., min_length=3)
    service_description: str = Field(..., min_length=20)
    pricing_model: str = ""
    payment_terms: str = ""
    contact_email: str = ""
    jurisdiction: str = "Polska"
    b2b_only: bool = False
    subscription_based: bool = False
    free_trial: bool = False
    refund_policy: str = ""


class ReturnPolicyRequest(BaseModel):
    """Request for return policy generation."""
    business_type: str = "ecommerce"
    products_type: str = ""
    return_period_days: int = Field(default=14, ge=7, le=365)
    accepts_opened_products: bool = True
    free_returns: bool = False
    contact_email: str = ""


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/contract/review")
async def review_contract_endpoint(
    data: ContractReviewRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Review a contract and identify risks."""
    result = await review_contract(
        contract_text=data.contract_text,
        contract_type=data.contract_type,
        your_role=data.your_role,
        key_concerns=data.key_concerns,
        industry=data.industry,
    )

    return result


@router.post("/contract/compare")
async def compare_contracts_endpoint(
    data: ContractCompareRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Compare two versions of a contract."""
    result = await compare_contracts(
        contract_a=data.contract_a,
        contract_b=data.contract_b,
        contract_type=data.contract_type,
    )

    return result


@router.post("/gdpr/check")
async def check_gdpr_endpoint(
    data: GDPRCheckRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Check GDPR compliance for a business."""
    result = await check_gdpr_compliance(
        business_description=data.business_description,
        data_collected=data.data_collected,
        data_processing_purposes=data.data_processing_purposes,
        third_party_sharing=data.third_party_sharing,
        has_privacy_policy=data.has_privacy_policy,
        has_consent_mechanism=data.has_consent_mechanism,
        stores_data_outside_eu=data.stores_data_outside_eu,
    )

    return result


@router.post("/privacy-policy")
async def generate_privacy_policy_endpoint(
    data: PrivacyPolicyRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Generate a GDPR-compliant privacy policy."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": current_user.company_id})
    company_name = company.get("name", "") if company else ""

    result = await generate_privacy_policy(
        company_name=company_name,
        company_address=data.company_address,
        business_type=data.business_type,
        data_collected=data.data_collected,
        data_purposes=data.data_purposes,
        third_parties=data.third_parties,
        cookies_used=data.cookies_used,
        analytics_tools=data.analytics_tools,
        contact_email=data.contact_email,
        iod_contact=data.iod_contact,
    )

    return result


@router.post("/dpa")
async def generate_dpa_endpoint(
    data: DPARequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Generate a Data Processing Agreement (DPA)."""
    result = await generate_data_processing_agreement(
        controller_name=data.controller_name,
        controller_address=data.controller_address,
        processor_name=data.processor_name,
        processor_address=data.processor_address,
        processing_subject=data.processing_subject,
        data_categories=data.data_categories,
        data_subjects=data.data_subjects,
        processing_duration=data.processing_duration,
    )

    return result


@router.post("/terms-of-service")
async def generate_terms_endpoint(
    data: TermsOfServiceRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Generate Terms of Service document."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": current_user.company_id})
    company_name = company.get("name", "") if company else ""

    result = await generate_terms_of_service(
        company_name=company_name,
        company_address=data.company_address,
        service_type=data.service_type,
        service_description=data.service_description,
        pricing_model=data.pricing_model,
        payment_terms=data.payment_terms,
        contact_email=data.contact_email,
        jurisdiction=data.jurisdiction,
        b2b_only=data.b2b_only,
        subscription_based=data.subscription_based,
        free_trial=data.free_trial,
        refund_policy=data.refund_policy,
    )

    return result


@router.post("/return-policy")
async def generate_return_policy_endpoint(
    data: ReturnPolicyRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Generate a return/refund policy."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": current_user.company_id})
    company_name = company.get("name", "") if company else ""

    result = await generate_return_policy(
        company_name=company_name,
        business_type=data.business_type,
        products_type=data.products_type,
        return_period_days=data.return_period_days,
        accepts_opened_products=data.accepts_opened_products,
        free_returns=data.free_returns,
        contact_email=data.contact_email,
    )

    return result

"""HR Department API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.agents.hr import (
    generate_job_posting,
    research_salary_market,
    generate_interview_questions,
    generate_onboarding_plan,
)

router = APIRouter(prefix="/hr", tags=["hr"])


# ============================================================================
# SCHEMAS
# ============================================================================


class JobPostingRequest(BaseModel):
    """Request for generating a job posting."""
    position: str = Field(..., min_length=2)
    department: str = Field(..., min_length=2)
    requirements: list[str] = Field(..., min_length=1)
    responsibilities: list[str] = Field(..., min_length=1)
    location: str = "Polska"
    employment_type: str = "pełny etat"
    experience_level: str = "mid"
    salary_range: str = ""
    benefits: list[str] | None = None
    use_web_search: bool = True


class SalaryResearchRequest(BaseModel):
    """Request for salary market research."""
    position: str = Field(..., min_length=2)
    location: str = "Polska"
    experience_level: str = "mid"


class InterviewQuestionsRequest(BaseModel):
    """Request for interview questions."""
    position: str = Field(..., min_length=2)
    department: str = Field(..., min_length=2)
    experience_level: str = "mid"
    skills: list[str] | None = None
    interview_type: str = "technical"
    company_values: list[str] | None = None
    duration_minutes: int = Field(default=60, ge=15, le=180)
    use_web_search: bool = True


class OnboardingPlanRequest(BaseModel):
    """Request for onboarding plan."""
    position: str = Field(..., min_length=2)
    department: str = Field(..., min_length=2)
    employee_name: str = ""
    start_date: str = ""
    manager_name: str = ""
    buddy_name: str = ""
    onboarding_duration_days: int = Field(default=30, ge=7, le=90)
    remote: bool = False
    tools_and_systems: list[str] | None = None
    team_members: list[str] | None = None


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/job-posting")
async def create_job_posting(
    data: JobPostingRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Generate a professional job posting."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Get company info for context
    company = await db.companies.find_one({"_id": current_user.company_id})
    company_name = company.get("name", "") if company else ""
    company_description = company.get("description", "") if company else ""

    result = await generate_job_posting(
        position=data.position,
        department=data.department,
        requirements=data.requirements,
        responsibilities=data.responsibilities,
        company_name=company_name,
        company_description=company_description,
        location=data.location,
        employment_type=data.employment_type,
        experience_level=data.experience_level,
        salary_range=data.salary_range,
        benefits=data.benefits,
        use_web_search=data.use_web_search,
    )

    return result


@router.post("/salary-research")
async def get_salary_research(
    data: SalaryResearchRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Research salary market for a position."""
    result = await research_salary_market(
        position=data.position,
        location=data.location,
        experience_level=data.experience_level,
    )

    return result


@router.post("/interview-questions")
async def create_interview_questions(
    data: InterviewQuestionsRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Generate interview questions for a position."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Get company values if available
    company = await db.companies.find_one({"_id": current_user.company_id})
    company_values = data.company_values
    if not company_values and company:
        brand = company.get("brand_settings", {})
        company_values = brand.get("values", [])

    result = await generate_interview_questions(
        position=data.position,
        department=data.department,
        experience_level=data.experience_level,
        skills=data.skills,
        interview_type=data.interview_type,
        company_values=company_values,
        duration_minutes=data.duration_minutes,
        use_web_search=data.use_web_search,
    )

    return result


@router.post("/onboarding-plan")
async def create_onboarding_plan(
    data: OnboardingPlanRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Generate an onboarding plan for a new employee."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": current_user.company_id})
    company_name = company.get("name", "") if company else ""

    result = await generate_onboarding_plan(
        position=data.position,
        department=data.department,
        employee_name=data.employee_name,
        start_date=data.start_date,
        manager_name=data.manager_name,
        buddy_name=data.buddy_name,
        company_name=company_name,
        onboarding_duration_days=data.onboarding_duration_days,
        remote=data.remote,
        tools_and_systems=data.tools_and_systems,
        team_members=data.team_members,
    )

    return result

"""HR Department AI Agents.

Agents for human resources tasks:
- Recruiter: Job postings and candidate sourcing
- Interviewer: Interview question preparation
- Onboarding: Onboarding materials and checklists
"""

from app.services.agents.hr.recruiter import generate_job_posting, research_salary_market
from app.services.agents.hr.interviewer import generate_interview_questions
from app.services.agents.hr.onboarding import generate_onboarding_plan

__all__ = [
    "generate_job_posting",
    "research_salary_market",
    "generate_interview_questions",
    "generate_onboarding_plan",
]

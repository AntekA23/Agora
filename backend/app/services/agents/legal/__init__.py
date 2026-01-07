"""Legal Department AI Agents.

Agents for legal tasks:
- Contract Reviewer: Analyzing contracts and identifying risks
- GDPR Assistant: GDPR compliance checks and recommendations
- Terms Generator: Generating terms of service and policies
"""

from app.services.agents.legal.contract_reviewer import (
    review_contract,
    compare_contracts,
)
from app.services.agents.legal.gdpr_assistant import (
    check_gdpr_compliance,
    generate_privacy_policy,
    generate_data_processing_agreement,
)
from app.services.agents.legal.terms_generator import (
    generate_terms_of_service,
    generate_return_policy,
)

__all__ = [
    "review_contract",
    "compare_contracts",
    "check_gdpr_compliance",
    "generate_privacy_policy",
    "generate_data_processing_agreement",
    "generate_terms_of_service",
    "generate_return_policy",
]

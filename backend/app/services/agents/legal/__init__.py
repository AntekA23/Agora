"""Legal Department AI Agents - Zgodne z polskim prawem.

Agenci dla zadań prawnych:
- Contract Reviewer: Analiza umów według KC, KP, ustawy o prawach konsumenta
- GDPR Assistant: Zgodność z RODO/GDPR i polskim prawem ochrony danych (UODO)
- Terms Generator: Regulaminy zgodne z UŚUDE i ustawą o prawach konsumenta

Podstawy prawne:
- Kodeks cywilny (KC)
- Kodeks pracy (KP)
- Ustawa o prawach konsumenta
- Ustawa o świadczeniu usług drogą elektroniczną (UŚUDE)
- RODO (Rozporządzenie 2016/679)
- Ustawa o ochronie danych osobowych (UODO)
"""

# Contract Reviewer - analiza umów
from app.services.agents.legal.contract_reviewer import (
    review_contract,
    analyze_employment_contract,
    check_abusive_clauses,
    compare_contracts,
    POLISH_LEGAL_BASES,
    COMMON_ABUSIVE_CLAUSES,
    STATUTE_OF_LIMITATIONS,
)

# GDPR/RODO Assistant - ochrona danych osobowych
from app.services.agents.legal.gdpr_assistant import (
    check_gdpr_compliance,
    generate_privacy_policy,
    generate_data_processing_agreement,
    generate_rcpd_template,
    RODO_ARTICLES,
    POLISH_DATA_PROTECTION_LAW,
    IOD_REQUIRED_CASES,
    DPIA_REQUIRED_CASES,
)

# Terms Generator - regulaminy i polityki
from app.services.agents.legal.terms_generator import (
    generate_terms_of_service,
    generate_return_policy,
    generate_marketing_consents,
    generate_data_collection_notice,
    POLISH_ECOMMERCE_LAW,
    WITHDRAWAL_EXCEPTIONS,
    REQUIRED_CONSUMER_INFO,
    WITHDRAWAL_FORM_TEMPLATE,
)

__all__ = [
    # Contract Reviewer
    "review_contract",
    "analyze_employment_contract",
    "check_abusive_clauses",
    "compare_contracts",
    "POLISH_LEGAL_BASES",
    "COMMON_ABUSIVE_CLAUSES",
    "STATUTE_OF_LIMITATIONS",

    # GDPR/RODO Assistant
    "check_gdpr_compliance",
    "generate_privacy_policy",
    "generate_data_processing_agreement",
    "generate_rcpd_template",
    "RODO_ARTICLES",
    "POLISH_DATA_PROTECTION_LAW",
    "IOD_REQUIRED_CASES",
    "DPIA_REQUIRED_CASES",

    # Terms Generator
    "generate_terms_of_service",
    "generate_return_policy",
    "generate_marketing_consents",
    "generate_data_collection_notice",
    "POLISH_ECOMMERCE_LAW",
    "WITHDRAWAL_EXCEPTIONS",
    "REQUIRED_CONSUMER_INFO",
    "WITHDRAWAL_FORM_TEMPLATE",
]

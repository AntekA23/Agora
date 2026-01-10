"""GDPR/RODO Assistant Agent - Polish data protection compliance.

This module provides GDPR/RODO compliance assistance specifically for Polish context:
- RODO (Rozporządzenie o Ochronie Danych Osobowych) - EU GDPR in Polish
- UODO (Urząd Ochrony Danych Osobowych) - Polish Data Protection Authority
- RCPD (Rejestr Czynności Przetwarzania Danych) - Processing Activities Register
- DPIA (Ocena Skutków dla Ochrony Danych) - Data Protection Impact Assessment
- IOD (Inspektor Ochrony Danych) - Data Protection Officer requirements
"""

import json
import re
from datetime import datetime
from typing import Any

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


# =============================================================================
# POLISH RODO/GDPR LEGAL FRAMEWORK
# =============================================================================

RODO_ARTICLES = {
    "podstawy_przetwarzania": {
        "article": "Art. 6 RODO",
        "title": "Zgodność przetwarzania z prawem",
        "bases": [
            "zgoda (Art. 6 ust. 1 lit. a)",
            "wykonanie umowy (Art. 6 ust. 1 lit. b)",
            "obowiązek prawny (Art. 6 ust. 1 lit. c)",
            "ochrona żywotnych interesów (Art. 6 ust. 1 lit. d)",
            "zadanie publiczne (Art. 6 ust. 1 lit. e)",
            "prawnie uzasadniony interes (Art. 6 ust. 1 lit. f)",
        ],
    },
    "dane_szczegolne": {
        "article": "Art. 9 RODO",
        "title": "Szczególne kategorie danych",
        "categories": [
            "pochodzenie rasowe/etniczne",
            "poglądy polityczne",
            "przekonania religijne/światopoglądowe",
            "przynależność do związków zawodowych",
            "dane genetyczne",
            "dane biometryczne",
            "dane dotyczące zdrowia",
            "dane dotyczące seksualności",
        ],
    },
    "prawa_osob": {
        "article": "Art. 12-22 RODO",
        "rights": {
            "informacja": "Art. 13-14 - Prawo do informacji",
            "dostep": "Art. 15 - Prawo dostępu",
            "sprostowanie": "Art. 16 - Prawo do sprostowania",
            "usuniecie": "Art. 17 - Prawo do usunięcia (bycie zapomnianym)",
            "ograniczenie": "Art. 18 - Prawo do ograniczenia przetwarzania",
            "przenoszenie": "Art. 20 - Prawo do przenoszenia danych",
            "sprzeciw": "Art. 21 - Prawo do sprzeciwu",
            "profilowanie": "Art. 22 - Zautomatyzowane decyzje i profilowanie",
        },
    },
    "obowiazki_administratora": {
        "article": "Art. 24-43 RODO",
        "obligations": {
            "rcpd": "Art. 30 - Rejestr czynności przetwarzania",
            "bezpieczenstwo": "Art. 32 - Bezpieczeństwo przetwarzania",
            "naruszenia": "Art. 33-34 - Zgłaszanie naruszeń (72h do UODO)",
            "dpia": "Art. 35 - Ocena skutków dla ochrony danych",
            "iod": "Art. 37-39 - Inspektor Ochrony Danych",
            "powierzenie": "Art. 28 - Umowa powierzenia przetwarzania",
        },
    },
    "transfer_danych": {
        "article": "Art. 44-49 RODO",
        "mechanisms": [
            "Decyzja o adekwatności (Art. 45)",
            "Standardowe klauzule umowne (Art. 46)",
            "Wiążące reguły korporacyjne (Art. 47)",
            "Wyjątki (Art. 49)",
        ],
    },
}

# Polskie przepisy uzupełniające RODO
POLISH_DATA_PROTECTION_LAW = {
    "ustawa": "Ustawa z dnia 10 maja 2018 r. o ochronie danych osobowych",
    "uodo": {
        "name": "Urząd Ochrony Danych Osobowych",
        "address": "ul. Stawki 2, 00-193 Warszawa",
        "website": "https://uodo.gov.pl",
        "complaint_info": "Skarga do Prezesa UODO (Art. 77 RODO)",
    },
    "kary": {
        "max_tier_1": "do 10 000 000 EUR lub 2% obrotu",
        "max_tier_2": "do 20 000 000 EUR lub 4% obrotu",
        "polish_public": "do 100 000 PLN dla podmiotów publicznych",
    },
}

# Kiedy wymagany jest IOD (Art. 37 RODO)
IOD_REQUIRED_CASES = [
    "Organ lub podmiot publiczny",
    "Główna działalność polega na przetwarzaniu wymagającym regularnego monitorowania osób na dużą skalę",
    "Główna działalność polega na przetwarzaniu danych szczególnych kategorii na dużą skalę",
    "Główna działalność polega na przetwarzaniu danych o wyrokach skazujących na dużą skalę",
]

# Kiedy wymagana jest DPIA (Art. 35 RODO)
DPIA_REQUIRED_CASES = [
    "Systematyczna, kompleksowa ocena osób oparta na zautomatyzowanym przetwarzaniu (profilowanie)",
    "Przetwarzanie na dużą skalę danych szczególnych kategorii",
    "Systematyczne monitorowanie miejsc dostępnych publicznie na dużą skalę",
    "Nowe technologie, które mogą powodować wysokie ryzyko",
    "Ocenianie lub punktowanie (scoring)",
    "Podejmowanie zautomatyzowanych decyzji ze skutkiem prawnym",
    "Śledzenie lokalizacji lub zachowania",
    "Dane dzieci lub innych osób wymagających szczególnej ochrony",
]


def _get_llm():
    """Get LLM instance for GDPR analysis."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY,
    )


def _build_rodo_context() -> str:
    """Build RODO legal context for the agent."""
    lines = ["PODSTAWY PRAWNE RODO:"]

    for key, data in RODO_ARTICLES.items():
        lines.append(f"\n{data['article']} - {data['title']}:")
        if "bases" in data:
            for base in data["bases"]:
                lines.append(f"  - {base}")
        if "rights" in data:
            for right_key, right_desc in data["rights"].items():
                lines.append(f"  - {right_desc}")
        if "obligations" in data:
            for obl_key, obl_desc in data["obligations"].items():
                lines.append(f"  - {obl_desc}")

    lines.append("\nPOLSKIE PRZEPISY:")
    lines.append(f"  - {POLISH_DATA_PROTECTION_LAW['ustawa']}")
    lines.append(f"  - {POLISH_DATA_PROTECTION_LAW['uodo']['name']}: {POLISH_DATA_PROTECTION_LAW['uodo']['website']}")

    return "\n".join(lines)


async def check_gdpr_compliance(
    business_description: str,
    data_collected: list[str],
    data_processing_purposes: list[str],
    third_party_sharing: list[str] | None = None,
    has_privacy_policy: bool = False,
    has_consent_mechanism: bool = False,
    stores_data_outside_eu: bool = False,
    number_of_data_subjects: str = "unknown",
    uses_profiling: bool = False,
    processes_special_categories: bool = False,
    is_public_entity: bool = False,
) -> dict[str, Any]:
    """Check GDPR/RODO compliance for a Polish business.

    Args:
        business_description: Description of the business
        data_collected: Types of personal data collected
        data_processing_purposes: Purposes for data processing
        third_party_sharing: Third parties data is shared with
        has_privacy_policy: Whether a privacy policy exists
        has_consent_mechanism: Whether consent mechanism exists
        stores_data_outside_eu: Whether data is stored outside EU
        number_of_data_subjects: Approximate number (e.g., "<1000", "1000-10000", ">10000")
        uses_profiling: Whether profiling is used
        processes_special_categories: Whether special category data is processed
        is_public_entity: Whether this is a public entity

    Returns:
        Dictionary with comprehensive RODO compliance assessment
    """
    llm = _get_llm()

    rodo_context = _build_rodo_context()

    iod_cases = "\n".join([f"  - {case}" for case in IOD_REQUIRED_CASES])
    dpia_cases = "\n".join([f"  - {case}" for case in DPIA_REQUIRED_CASES])

    gdpr_expert = Agent(
        role="Ekspert RODO / Inspektor Ochrony Danych",
        goal="Przeprowadzać audyty zgodności z RODO i polskimi przepisami o ochronie danych",
        backstory=f"""Jesteś certyfikowanym Inspektorem Ochrony Danych (IOD) z 10-letnim
        doświadczeniem w Polsce. Specjalizujesz się w:
        - RODO (Rozporządzenie 2016/679)
        - Polskiej ustawie o ochronie danych osobowych (2018)
        - Wytycznych UODO i EROD

        {rodo_context}

        KIEDY WYMAGANY IOD (Art. 37 RODO):
        {iod_cases}

        KIEDY WYMAGANA DPIA (Art. 35 RODO):
        {dpia_cases}

        KARY:
        - Tier 1: do 10 mln EUR lub 2% obrotu (Art. 83 ust. 4 RODO)
        - Tier 2: do 20 mln EUR lub 4% obrotu (Art. 83 ust. 5 RODO)
        - Podmioty publiczne w Polsce: do 100 000 PLN

        WAŻNE: Twoja analiza ma charakter informacyjny. Zalecasz pełny audyt RODO.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    data_text = "\n".join([f"- {d}" for d in data_collected])
    purposes_text = "\n".join([f"- {p}" for p in data_processing_purposes])
    sharing_text = "\n".join([f"- {s}" for s in (third_party_sharing or ["brak"])])

    task = Task(
        description=f"""
        Przeprowadź kompleksową ocenę zgodności z RODO:

        OPIS DZIAŁALNOŚCI:
        {business_description}

        ZBIERANE DANE OSOBOWE:
        {data_text}

        CELE PRZETWARZANIA:
        {purposes_text}

        UDOSTĘPNIANIE DANYCH:
        {sharing_text}

        SKALA PRZETWARZANIA:
        - Liczba osób: {number_of_data_subjects}
        - Podmiot publiczny: {"TAK" if is_public_entity else "NIE"}
        - Profilowanie: {"TAK" if uses_profiling else "NIE"}
        - Dane szczególne: {"TAK" if processes_special_categories else "NIE"}
        - Transfer poza UE: {"TAK" if stores_data_outside_eu else "NIE"}

        OBECNY STAN:
        - Polityka prywatności: {"TAK" if has_privacy_policy else "NIE"}
        - Mechanizm zgód: {"TAK" if has_consent_mechanism else "NIE"}

        PRZEPROWADŹ AUDYT W OBSZARACH:

        1. PODSTAWY PRAWNE PRZETWARZANIA (Art. 6 RODO)
           - Czy każdy cel ma właściwą podstawę?
           - Czy zgody są poprawnie zbierane?

        2. OBOWIĄZKI INFORMACYJNE (Art. 13-14 RODO)
           - Czy polityka prywatności jest kompletna?
           - Czy spełnia wymogi formalne?

        3. PRAWA OSÓB (Art. 15-22 RODO)
           - Czy zapewniono realizację wszystkich praw?
           - Czy są procedury obsługi żądań?

        4. BEZPIECZEŃSTWO (Art. 32 RODO)
           - Środki techniczne i organizacyjne
           - Pseudonimizacja, szyfrowanie

        5. DOKUMENTACJA (Art. 30 RODO - RCPD)
           - Czy prowadzony jest rejestr czynności?

        6. IOD - INSPEKTOR OCHRONY DANYCH (Art. 37 RODO)
           - Czy wymagane wyznaczenie IOD?

        7. DPIA - OCENA SKUTKÓW (Art. 35 RODO)
           - Czy wymagana DPIA?

        8. TRANSFER DANYCH (Art. 44-49 RODO)
           - Czy transfer poza UE jest zgodny?

        9. UMOWY POWIERZENIA (Art. 28 RODO)
           - Czy są umowy z procesorami?

        Zwróć w formacie JSON:
        {{
            "overall_compliance": {{
                "score": 0-100,
                "status": "compliant/partially_compliant/non_compliant",
                "critical_issues": liczba,
                "high_issues": liczba,
                "medium_issues": liczba
            }},
            "legal_bases_assessment": {{
                "status": "ok/issues",
                "purposes_with_bases": [
                    {{
                        "purpose": "cel",
                        "suggested_legal_basis": "podstawa z Art. 6 RODO",
                        "valid": true/false,
                        "notes": "uwagi"
                    }}
                ],
                "issues": ["problemy"]
            }},
            "areas": [
                {{
                    "area": "nazwa obszaru",
                    "rodo_articles": ["artykuły RODO"],
                    "status": "compliant/warning/non_compliant",
                    "current_state": "obecny stan",
                    "requirements": ["wymagania"],
                    "gaps": ["braki"],
                    "recommendations": ["rekomendacje"]
                }}
            ],
            "iod_assessment": {{
                "required": true/false,
                "reasons": ["powody"],
                "recommendation": "rekomendacja"
            }},
            "dpia_assessment": {{
                "required": true/false,
                "triggers": ["czynniki wymagające DPIA"],
                "recommendation": "rekomendacja"
            }},
            "required_documents": [
                {{
                    "document": "nazwa dokumentu",
                    "rodo_basis": "podstawa w RODO",
                    "required": true/false,
                    "exists": true/false,
                    "priority": "critical/high/medium"
                }}
            ],
            "action_plan": [
                {{
                    "action": "co zrobić",
                    "rodo_article": "artykuł RODO",
                    "priority": "critical/high/medium/low",
                    "deadline_category": "natychmiast/30dni/90dni",
                    "responsible": "kto",
                    "estimated_effort": "niski/średni/wysoki"
                }}
            ],
            "risk_assessment": {{
                "uodo_inspection_risk": "low/medium/high",
                "fine_risk_tier": "none/tier1/tier2",
                "max_potential_fine": "kwota",
                "main_risk_factors": ["czynniki"]
            }},
            "uodo_info": {{
                "name": "Urząd Ochrony Danych Osobowych",
                "website": "https://uodo.gov.pl",
                "complaint_right": "Art. 77 RODO - prawo do skargi"
            }},
            "disclaimer": "Ocena ma charakter informacyjny. Zalecamy przeprowadzenie pełnego audytu RODO przez certyfikowanego IOD."
        }}
        """,
        agent=gdpr_expert,
        expected_output="Comprehensive RODO compliance assessment in JSON format",
    )

    crew = Crew(
        agents=[gdpr_expert],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    result_text = str(result)

    json_match = re.search(r"\{[\s\S]*\}", result_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return {"success": True, "assessment": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "assessment": {"raw_content": result_text}}


async def generate_privacy_policy(
    company_name: str,
    company_address: str,
    company_nip: str = "",
    business_type: str = "",
    data_collected: list[str] | None = None,
    data_purposes: list[str] | None = None,
    legal_bases: list[str] | None = None,
    third_parties: list[str] | None = None,
    cookies_used: bool = True,
    analytics_tools: list[str] | None = None,
    contact_email: str = "",
    iod_name: str = "",
    iod_email: str = "",
    data_retention_periods: dict[str, str] | None = None,
    transfers_outside_eu: bool = False,
    transfer_countries: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a RODO-compliant privacy policy for Polish business.

    Args:
        company_name: Company legal name
        company_address: Company address
        company_nip: Company NIP (tax ID)
        business_type: Type of business/website
        data_collected: Types of personal data collected
        data_purposes: Purposes for data processing
        legal_bases: Legal bases for processing (Art. 6 RODO)
        third_parties: Third parties receiving data
        cookies_used: Whether cookies are used
        analytics_tools: Analytics tools used
        contact_email: Contact email for privacy matters
        iod_name: Data Protection Officer name (if appointed)
        iod_email: DPO contact email
        data_retention_periods: Retention periods by data type
        transfers_outside_eu: Whether data is transferred outside EU
        transfer_countries: Countries where data is transferred

    Returns:
        Dictionary with complete privacy policy
    """
    llm = _get_llm()

    rodo_rights = "\n".join([
        f"  - {desc}" for desc in RODO_ARTICLES["prawa_osob"]["rights"].values()
    ])

    policy_writer = Agent(
        role="Specjalista ds. Polityki Prywatności RODO",
        goal="Tworzyć kompleksowe polityki prywatności zgodne z RODO i polskim prawem",
        backstory=f"""Jesteś specjalistą od tworzenia dokumentacji RODO dla polskich firm.
        Tworzysz polityki prywatności, które są:
        - Zgodne z Art. 13-14 RODO
        - Zrozumiałe dla przeciętnego użytkownika
        - Kompletne pod względem prawnym

        WYMAGANE INFORMACJE WG ART. 13 RODO:
        1. Tożsamość i dane kontaktowe administratora
        2. Dane kontaktowe IOD (jeśli wyznaczony)
        3. Cele przetwarzania i podstawy prawne
        4. Prawnie uzasadnione interesy (jeśli Art. 6.1.f)
        5. Odbiorcy danych
        6. Transfer do państw trzecich
        7. Okres przechowywania
        8. Prawa osoby:
        {rodo_rights}
        9. Prawo do cofnięcia zgody
        10. Prawo do skargi do UODO
        11. Informacja o obowiązku/dobrowolności podania danych
        12. Informacja o profilowaniu

        UODO: {POLISH_DATA_PROTECTION_LAW['uodo']['name']}
        Adres: {POLISH_DATA_PROTECTION_LAW['uodo']['address']}""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    data_text = "\n".join([f"- {d}" for d in (data_collected or ["dane kontaktowe"])])
    purposes_text = "\n".join([f"- {p}" for p in (data_purposes or ["realizacja usługi"])])
    bases_text = "\n".join([f"- {b}" for b in (legal_bases or ["zgoda", "wykonanie umowy"])])
    third_parties_text = "\n".join([f"- {t}" for t in (third_parties or [])])
    analytics_text = ", ".join(analytics_tools or ["brak"])
    retention_text = "\n".join([
        f"- {k}: {v}" for k, v in (data_retention_periods or {}).items()
    ]) or "Zgodnie z celami przetwarzania"
    transfer_countries_text = ", ".join(transfer_countries or [])

    task = Task(
        description=f"""
        Stwórz politykę prywatności zgodną z RODO (Art. 13-14):

        ADMINISTRATOR DANYCH:
        - Nazwa: {company_name}
        - Adres: {company_address}
        - NIP: {company_nip or "[NIP]"}
        - Email: {contact_email or "[EMAIL]"}
        - Typ działalności: {business_type or "usługi online"}

        IOD (Inspektor Ochrony Danych):
        - Imię i nazwisko: {iod_name or "nie wyznaczono"}
        - Email: {iod_email or "nie dotyczy"}

        ZBIERANE DANE:
        {data_text}

        CELE PRZETWARZANIA:
        {purposes_text}

        PODSTAWY PRAWNE (Art. 6 RODO):
        {bases_text}

        ODBIORCY DANYCH:
        {third_parties_text or "Dane nie są udostępniane podmiotom trzecim"}

        COOKIES: {"Tak" if cookies_used else "Nie"}
        NARZĘDZIA ANALYTICS: {analytics_text}

        OKRES PRZECHOWYWANIA:
        {retention_text}

        TRANSFER POZA UE: {"Tak - kraje: " + transfer_countries_text if transfers_outside_eu else "Nie"}

        POLITYKA MUSI ZAWIERAĆ WSZYSTKIE ELEMENTY Z ART. 13 RODO:

        1. ADMINISTRATOR DANYCH (§1)
        2. INSPEKTOR OCHRONY DANYCH (§2) - jeśli wyznaczony
        3. CELE I PODSTAWY PRAWNE PRZETWARZANIA (§3)
        4. KATEGORIE DANYCH (§4)
        5. ODBIORCY DANYCH (§5)
        6. TRANSFER DO PAŃSTW TRZECICH (§6)
        7. OKRES PRZECHOWYWANIA (§7)
        8. PRAWA OSOBY KTÓREJ DANE DOTYCZĄ (§8)
           - prawo dostępu (Art. 15)
           - prawo sprostowania (Art. 16)
           - prawo usunięcia (Art. 17)
           - prawo ograniczenia (Art. 18)
           - prawo przenoszenia (Art. 20)
           - prawo sprzeciwu (Art. 21)
           - prawo cofnięcia zgody
           - prawo skargi do UODO
        9. OBOWIĄZEK PODANIA DANYCH (§9)
        10. PROFILOWANIE (§10)
        11. PLIKI COOKIES (§11) - jeśli dotyczy
        12. ZMIANY POLITYKI (§12)
        13. KONTAKT (§13)

        Zwróć w formacie JSON:
        {{
            "title": "Polityka Prywatności",
            "administrator": {{
                "name": "{company_name}",
                "address": "{company_address}",
                "nip": "{company_nip or '[NIP]'}",
                "email": "{contact_email or '[EMAIL]'}"
            }},
            "iod": {{
                "appointed": {"true" if iod_name else "false"},
                "name": "{iod_name or 'nie wyznaczono'}",
                "email": "{iod_email or ''}"
            }},
            "last_updated": "{datetime.now().strftime('%d.%m.%Y')}",
            "sections": [
                {{
                    "number": "§ 1",
                    "title": "tytuł sekcji",
                    "rodo_basis": "podstawa w RODO",
                    "content_html": "treść sekcji w HTML"
                }}
            ],
            "full_text": "pełna treść polityki jako tekst",
            "full_html": "pełna treść jako HTML",
            "required_consents": [
                {{
                    "purpose": "cel",
                    "consent_text": "treść zgody",
                    "required": true/false
                }}
            ],
            "cookie_policy": {{
                "included": {"true" if cookies_used else "false"},
                "cookie_types": ["typy cookies"],
                "cookie_table": [
                    {{
                        "name": "nazwa",
                        "provider": "dostawca",
                        "purpose": "cel",
                        "expiry": "czas życia",
                        "type": "necessary/functional/analytics/marketing"
                    }}
                ]
            }},
            "compliance_checklist": [
                {{
                    "requirement": "wymóg RODO",
                    "article": "artykuł",
                    "fulfilled": true/false
                }}
            ]
        }}
        """,
        agent=policy_writer,
        expected_output="Complete RODO-compliant privacy policy in JSON format",
    )

    crew = Crew(
        agents=[policy_writer],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    result_text = str(result)

    json_match = re.search(r"\{[\s\S]*\}", result_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return {"success": True, "privacy_policy": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "privacy_policy": {"full_text": result_text}}


async def generate_data_processing_agreement(
    controller_name: str,
    controller_address: str,
    controller_nip: str = "",
    processor_name: str = "",
    processor_address: str = "",
    processor_nip: str = "",
    processing_subject: str = "",
    data_categories: list[str] | None = None,
    data_subjects: list[str] | None = None,
    processing_duration: str = "",
    processing_location: str = "Polska",
    subprocessors_allowed: bool = True,
    audit_rights: bool = True,
) -> dict[str, Any]:
    """Generate a Data Processing Agreement (DPA/Umowa Powierzenia) under Art. 28 RODO.

    Args:
        controller_name: Data controller company name
        controller_address: Controller address
        controller_nip: Controller NIP
        processor_name: Data processor company name
        processor_address: Processor address
        processor_nip: Processor NIP
        processing_subject: Subject of data processing
        data_categories: Categories of personal data
        data_subjects: Categories of data subjects
        processing_duration: Duration of processing
        processing_location: Location of processing
        subprocessors_allowed: Whether subprocessors are allowed
        audit_rights: Whether controller has audit rights

    Returns:
        Dictionary with complete DPA
    """
    llm = _get_llm()

    dpa_writer = Agent(
        role="Specjalista ds. Umów Powierzenia RODO",
        goal="Tworzyć umowy powierzenia przetwarzania danych zgodne z Art. 28 RODO",
        backstory="""Jesteś prawnikiem specjalizującym się w umowach IT i RODO.
        Tworzysz umowy powierzenia (DPA) zgodne z Art. 28 RODO.

        WYMOGI ART. 28 UST. 3 RODO - UMOWA MUSI OKREŚLAĆ:
        a) przedmiot i czas trwania przetwarzania
        b) charakter i cel przetwarzania
        c) rodzaj danych osobowych
        d) kategorie osób, których dane dotyczą
        e) obowiązki i prawa administratora

        ZOBOWIĄZANIA PROCESORA (Art. 28 ust. 3 lit. a-h):
        a) przetwarzanie wyłącznie na udokumentowane polecenie
        b) zobowiązanie osób do poufności
        c) bezpieczeństwo przetwarzania (Art. 32)
        d) warunki dalszego powierzenia
        e) pomoc w realizacji praw osób
        f) pomoc w DPIA i konsultacjach
        g) usunięcie/zwrot danych po zakończeniu
        h) udostępnienie informacji do audytu

        PODPOWIERZENIE (Art. 28 ust. 2 i 4):
        - Wymaga zgody administratora
        - Te same obowiązki co w głównej umowie
        - Odpowiedzialność procesora za podprocesora""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    data_text = "\n".join([f"- {d}" for d in (data_categories or ["dane kontaktowe"])])
    subjects_text = "\n".join([f"- {s}" for s in (data_subjects or ["klienci", "pracownicy"])])

    task = Task(
        description=f"""
        Stwórz umowę powierzenia przetwarzania danych (DPA) zgodną z Art. 28 RODO:

        ADMINISTRATOR DANYCH:
        - Nazwa: {controller_name}
        - Adres: {controller_address}
        - NIP: {controller_nip or "[NIP]"}

        PODMIOT PRZETWARZAJĄCY:
        - Nazwa: {processor_name or "[PROCESOR]"}
        - Adres: {processor_address or "[ADRES]"}
        - NIP: {processor_nip or "[NIP]"}

        PRZEDMIOT PRZETWARZANIA:
        {processing_subject or "Przetwarzanie danych w ramach świadczenia usług"}

        KATEGORIE DANYCH OSOBOWYCH:
        {data_text}

        KATEGORIE OSÓB:
        {subjects_text}

        CZAS PRZETWARZANIA: {processing_duration or "na czas trwania umowy głównej"}
        LOKALIZACJA: {processing_location}
        DALSZE POWIERZENIE: {"Dozwolone za zgodą" if subprocessors_allowed else "Niedozwolone"}
        PRAWO AUDYTU: {"Tak" if audit_rights else "Nie"}

        UMOWA MUSI ZAWIERAĆ (zgodnie z Art. 28 RODO):

        § 1. DEFINICJE I PRZEDMIOT UMOWY
        § 2. CZAS TRWANIA
        § 3. CHARAKTER I CEL PRZETWARZANIA
        § 4. RODZAJ DANYCH I KATEGORIE OSÓB
        § 5. OBOWIĄZKI ADMINISTRATORA
        § 6. OBOWIĄZKI PODMIOTU PRZETWARZAJĄCEGO
            - przetwarzanie na polecenie (Art. 28.3.a)
            - poufność (Art. 28.3.b)
            - bezpieczeństwo (Art. 28.3.c / Art. 32)
            - podpowierzenie (Art. 28.3.d)
            - pomoc w prawach osób (Art. 28.3.e)
            - pomoc w DPIA (Art. 28.3.f)
            - usunięcie danych (Art. 28.3.g)
            - audyt (Art. 28.3.h)
        § 7. DALSZE POWIERZENIE (podprocesorzy)
        § 8. PRZEKAZYWANIE DANYCH DO PAŃSTW TRZECICH
        § 9. NARUSZENIA OCHRONY DANYCH
        § 10. ODPOWIEDZIALNOŚĆ
        § 11. POSTANOWIENIA KOŃCOWE

        Zwróć w formacie JSON:
        {{
            "title": "Umowa Powierzenia Przetwarzania Danych Osobowych",
            "legal_basis": "Art. 28 Rozporządzenia (UE) 2016/679 (RODO)",
            "parties": {{
                "controller": {{
                    "role": "Administrator",
                    "name": "{controller_name}",
                    "address": "{controller_address}",
                    "nip": "{controller_nip or '[NIP]'}"
                }},
                "processor": {{
                    "role": "Podmiot Przetwarzający",
                    "name": "{processor_name or '[PROCESOR]'}",
                    "address": "{processor_address or '[ADRES]'}",
                    "nip": "{processor_nip or '[NIP]'}"
                }}
            }},
            "processing_details": {{
                "subject": "{processing_subject or 'Świadczenie usług'}",
                "duration": "{processing_duration or 'czas trwania umowy głównej'}",
                "location": "{processing_location}",
                "data_categories": {json.dumps(data_categories or ['dane kontaktowe'])},
                "data_subjects": {json.dumps(data_subjects or ['klienci'])}
            }},
            "sections": [
                {{
                    "number": "§ 1",
                    "title": "tytuł",
                    "rodo_basis": "artykuł RODO",
                    "content": "treść"
                }}
            ],
            "processor_obligations": [
                {{
                    "obligation": "obowiązek",
                    "rodo_article": "Art. 28.3.x",
                    "description": "opis"
                }}
            ],
            "full_text": "pełna treść umowy",
            "annexes": [
                {{
                    "annex_number": "Załącznik 1",
                    "title": "tytuł załącznika",
                    "content": "zawartość lub opis"
                }}
            ],
            "signatures": {{
                "controller_signature": "[podpis Administratora]",
                "processor_signature": "[podpis Podmiotu Przetwarzającego]",
                "date": "[data]",
                "place": "[miejsce]"
            }}
        }}
        """,
        agent=dpa_writer,
        expected_output="Complete DPA in JSON format",
    )

    crew = Crew(
        agents=[dpa_writer],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    result_text = str(result)

    json_match = re.search(r"\{[\s\S]*\}", result_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return {"success": True, "dpa": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "dpa": {"full_text": result_text}}


async def generate_rcpd_template(
    company_name: str,
    company_nip: str = "",
    iod_name: str = "",
    iod_contact: str = "",
    processing_activities: list[dict] | None = None,
) -> dict[str, Any]:
    """Generate RCPD (Rejestr Czynności Przetwarzania Danych) template.

    Art. 30 RODO requires maintaining a record of processing activities.

    Args:
        company_name: Company name
        company_nip: Company NIP
        iod_name: IOD name if appointed
        iod_contact: IOD contact details
        processing_activities: List of processing activities with details

    Returns:
        Dictionary with RCPD template
    """
    llm = _get_llm()

    rcpd_expert = Agent(
        role="Specjalista ds. Dokumentacji RODO",
        goal="Tworzyć rejestry czynności przetwarzania zgodne z Art. 30 RODO",
        backstory="""Jesteś specjalistą od dokumentacji RODO.
        Tworzysz RCPD zgodne z Art. 30 RODO.

        REJESTR ADMINISTRATORA (Art. 30 ust. 1) MUSI ZAWIERAĆ:
        a) imię/nazwisko lub nazwę oraz dane kontaktowe administratora
        b) cele przetwarzania
        c) opis kategorii osób i kategorii danych
        d) kategorie odbiorców
        e) przekazania do państw trzecich
        f) planowane terminy usunięcia
        g) ogólny opis środków bezpieczeństwa (Art. 32 ust. 1)

        ZWOLNIENIE Z OBOWIĄZKU (Art. 30 ust. 5):
        - przedsiębiorcy < 250 pracowników, CHYBA ŻE:
          - przetwarzanie może naruszać prawa osób
          - przetwarzanie nie jest sporadyczne
          - przetwarzanie obejmuje dane szczególne (Art. 9)""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    activities_text = ""
    if processing_activities:
        for i, act in enumerate(processing_activities, 1):
            activities_text += f"""
            {i}. {act.get('name', 'Czynność')}
               - Cel: {act.get('purpose', 'do określenia')}
               - Dane: {', '.join(act.get('data_categories', ['dane osobowe']))}
               - Osoby: {', '.join(act.get('data_subjects', ['klienci']))}
            """

    task = Task(
        description=f"""
        Stwórz szablon RCPD (Rejestr Czynności Przetwarzania Danych) zgodny z Art. 30 RODO:

        ADMINISTRATOR:
        - Nazwa: {company_name}
        - NIP: {company_nip or "[NIP]"}
        - IOD: {iod_name or "nie wyznaczono"}
        - Kontakt IOD: {iod_contact or "nie dotyczy"}

        ZNANE CZYNNOŚCI PRZETWARZANIA:
        {activities_text or "Do uzupełnienia"}

        STWÓRZ SZABLON RCPD ZAWIERAJĄCY:

        1. DANE ADMINISTRATORA
        2. DANE IOD (jeśli wyznaczony)
        3. TABELA CZYNNOŚCI PRZETWARZANIA z kolumnami:
           - Lp.
           - Nazwa czynności
           - Cel przetwarzania
           - Podstawa prawna (Art. 6 RODO)
           - Kategorie osób
           - Kategorie danych
           - Odbiorcy danych
           - Transfer poza UE (tak/nie + podstawa)
           - Termin usunięcia
           - Środki bezpieczeństwa

        Zwróć w formacie JSON:
        {{
            "title": "Rejestr Czynności Przetwarzania Danych Osobowych",
            "legal_basis": "Art. 30 ust. 1 RODO",
            "administrator": {{
                "name": "{company_name}",
                "nip": "{company_nip or '[NIP]'}",
                "address": "[adres]",
                "contact": "[email/telefon]"
            }},
            "iod": {{
                "appointed": {"true" if iod_name else "false"},
                "name": "{iod_name or 'nie wyznaczono'}",
                "contact": "{iod_contact or ''}"
            }},
            "last_updated": "{datetime.now().strftime('%d.%m.%Y')}",
            "processing_activities": [
                {{
                    "id": 1,
                    "activity_name": "nazwa czynności",
                    "purpose": "cel przetwarzania",
                    "legal_basis": "podstawa z Art. 6 RODO",
                    "data_subjects": ["kategorie osób"],
                    "data_categories": ["kategorie danych"],
                    "recipients": ["odbiorcy"],
                    "third_country_transfer": {{
                        "occurs": false,
                        "countries": [],
                        "safeguards": ""
                    }},
                    "retention_period": "okres przechowywania",
                    "security_measures": ["środki bezpieczeństwa"]
                }}
            ],
            "template_notes": [
                "Instrukcje wypełniania RCPD"
            ],
            "review_schedule": "Przegląd co najmniej raz w roku"
        }}
        """,
        agent=rcpd_expert,
        expected_output="RCPD template in JSON format",
    )

    crew = Crew(
        agents=[rcpd_expert],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    result_text = str(result)

    json_match = re.search(r"\{[\s\S]*\}", result_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return {"success": True, "rcpd": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "rcpd": {"raw_content": result_text}}

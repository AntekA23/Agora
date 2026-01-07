"""GDPR Assistant Agent - Compliance checks and policy generation."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.4,
        api_key=settings.OPENAI_API_KEY,
    )


async def check_gdpr_compliance(
    business_description: str,
    data_collected: list[str],
    data_processing_purposes: list[str],
    third_party_sharing: list[str] | None = None,
    has_privacy_policy: bool = False,
    has_consent_mechanism: bool = False,
    stores_data_outside_eu: bool = False,
) -> dict:
    """Check GDPR compliance for a business.

    Args:
        business_description: Description of the business
        data_collected: Types of personal data collected
        data_processing_purposes: Purposes for data processing
        third_party_sharing: Third parties data is shared with
        has_privacy_policy: Whether a privacy policy exists
        has_consent_mechanism: Whether consent mechanism exists
        stores_data_outside_eu: Whether data is stored outside EU

    Returns:
        Dictionary with compliance assessment
    """
    llm = _get_llm()

    gdpr_expert = Agent(
        role="GDPR Compliance Specialist",
        goal="Oceniać zgodność z RODO i dostarczać rekomendacje",
        backstory="""Jesteś ekspertem od ochrony danych osobowych z certyfikatem CIPP/E.
        Specjalizujesz się w RODO/GDPR dla polskich firm.
        Znasz wymogi UODO i praktyczne aspekty wdrożenia RODO.

        WAŻNE: Twoje analizy mają charakter informacyjny i nie zastępują
        audytu prawnego przez certyfikowanego IOD.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    data_text = "\n".join(f"- {d}" for d in data_collected)
    purposes_text = "\n".join(f"- {p}" for p in data_processing_purposes)
    sharing_text = "\n".join(f"- {s}" for s in (third_party_sharing or ["brak"]))

    task = Task(
        description=f"""
        Przeprowadź ocenę zgodności z RODO:

        OPIS DZIAŁALNOŚCI:
        {business_description}

        ZBIERANE DANE OSOBOWE:
        {data_text}

        CELE PRZETWARZANIA:
        {purposes_text}

        UDOSTĘPNIANIE DANYCH:
        {sharing_text}

        OBECNY STAN:
        - Polityka prywatności: {"TAK" if has_privacy_policy else "NIE"}
        - Mechanizm zgód: {"TAK" if has_consent_mechanism else "NIE"}
        - Dane poza UE: {"TAK" if stores_data_outside_eu else "NIE"}

        OCEŃ ZGODNOŚĆ W OBSZARACH:

        1. PODSTAWY PRAWNE PRZETWARZANIA (Art. 6 RODO)
        2. PRAWA OSÓB (Art. 12-22 RODO)
        3. OBOWIĄZKI INFORMACYJNE (Art. 13-14 RODO)
        4. BEZPIECZEŃSTWO DANYCH (Art. 32 RODO)
        5. DOKUMENTACJA (Art. 30 RODO)
        6. TRANSFER DANYCH (Art. 44-49 RODO)
        7. IOD - Inspektor Ochrony Danych (Art. 37-39 RODO)

        Zwróć w formacie JSON:
        {{
            "overall_compliance": {{
                "score": 0-100,
                "status": "compliant/partially_compliant/non_compliant",
                "critical_issues": liczba,
                "warnings": liczba
            }},
            "areas": [
                {{
                    "area": "nazwa obszaru",
                    "gdpr_articles": ["artykuły RODO"],
                    "status": "compliant/warning/non_compliant",
                    "findings": ["ustalenia"],
                    "requirements": ["wymagania do spełnienia"],
                    "recommendations": ["rekomendacje"]
                }}
            ],
            "required_documents": [
                {{
                    "document": "nazwa dokumentu",
                    "required": true/false,
                    "exists": true/false,
                    "priority": "critical/high/medium"
                }}
            ],
            "action_plan": [
                {{
                    "action": "co zrobić",
                    "priority": "critical/high/medium/low",
                    "deadline_suggestion": "sugerowany termin",
                    "responsible": "kto powinien"
                }}
            ],
            "potential_fines": {{
                "risk_level": "low/medium/high",
                "max_fine_tier": "do 10M EUR lub 2% obrotu / do 20M EUR lub 4% obrotu",
                "reasoning": "uzasadnienie"
            }},
            "iod_required": {{
                "required": true/false,
                "reasoning": "uzasadnienie"
            }},
            "disclaimer": "Ocena ma charakter informacyjny. Zalecany pełny audyt RODO."
        }}
        """,
        agent=gdpr_expert,
        expected_output="GDPR compliance assessment in JSON format",
    )

    crew = Crew(
        agents=[gdpr_expert],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    import json
    import re

    result_text = str(result)
    json_match = re.search(r'\{[\s\S]*\}', result_text)

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
    business_type: str,
    data_collected: list[str],
    data_purposes: list[str],
    third_parties: list[str] | None = None,
    cookies_used: bool = True,
    analytics_tools: list[str] | None = None,
    contact_email: str = "",
    iod_contact: str = "",
) -> dict:
    """Generate a GDPR-compliant privacy policy.

    Args:
        company_name: Company legal name
        company_address: Company address
        business_type: Type of business/website
        data_collected: Types of personal data collected
        data_purposes: Purposes for data processing
        third_parties: Third parties receiving data
        cookies_used: Whether cookies are used
        analytics_tools: Analytics tools used (Google Analytics, etc.)
        contact_email: Contact email for privacy matters
        iod_contact: Data Protection Officer contact

    Returns:
        Dictionary with privacy policy content
    """
    llm = _get_llm()

    policy_writer = Agent(
        role="Privacy Policy Specialist",
        goal="Tworzyć kompleksowe polityki prywatności zgodne z RODO",
        backstory="""Jesteś specjalistą od tworzenia dokumentacji RODO dla polskich firm.
        Piszesz polityki prywatności, które są jednocześnie zgodne z prawem
        i zrozumiałe dla zwykłego użytkownika. Używasz prostego języka.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    data_text = "\n".join(f"- {d}" for d in data_collected)
    purposes_text = "\n".join(f"- {p}" for p in data_purposes)
    third_parties_text = "\n".join(f"- {t}" for t in (third_parties or []))
    analytics_text = ", ".join(analytics_tools or ["brak"])

    task = Task(
        description=f"""
        Stwórz politykę prywatności zgodną z RODO:

        DANE FIRMY:
        - Nazwa: {company_name}
        - Adres: {company_address}
        - Typ działalności: {business_type}
        - Email kontaktowy: {contact_email or "[EMAIL]"}
        - IOD: {iod_contact or "nie wyznaczono"}

        ZBIERANE DANE:
        {data_text}

        CELE PRZETWARZANIA:
        {purposes_text}

        PODMIOTY TRZECIE:
        {third_parties_text or "Nie udostępniamy danych"}

        COOKIES: {"Tak" if cookies_used else "Nie"}
        NARZĘDZIA ANALYTICS: {analytics_text}

        POLITYKA MUSI ZAWIERAĆ (zgodnie z Art. 13 RODO):

        1. Dane administratora
        2. Dane kontaktowe IOD (jeśli wyznaczony)
        3. Cele przetwarzania i podstawy prawne
        4. Kategorie danych
        5. Odbiorcy danych
        6. Transfer do państw trzecich
        7. Okres przechowywania
        8. Prawa osób (dostęp, sprostowanie, usunięcie, etc.)
        9. Prawo do skargi do UODO
        10. Informacja o dobrowolności/obowiązku podania danych
        11. Informacja o profilowaniu (jeśli dotyczy)
        12. Polityka cookies (jeśli dotyczy)

        Zwróć w formacie JSON:
        {{
            "title": "Polityka Prywatności",
            "last_updated": "data",
            "sections": [
                {{
                    "number": "1",
                    "title": "tytuł sekcji",
                    "content": "treść sekcji w HTML"
                }}
            ],
            "full_text": "pełna treść polityki jako tekst",
            "full_html": "pełna treść jako HTML",
            "cookie_policy_section": "sekcja o cookies (jeśli dotyczy)"
        }}
        """,
        agent=policy_writer,
        expected_output="Privacy policy in JSON format",
    )

    crew = Crew(
        agents=[policy_writer],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    import json
    import re

    result_text = str(result)
    json_match = re.search(r'\{[\s\S]*\}', result_text)

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
    processor_name: str,
    processor_address: str,
    processing_subject: str,
    data_categories: list[str],
    data_subjects: list[str],
    processing_duration: str = "",
) -> dict:
    """Generate a Data Processing Agreement (DPA).

    Args:
        controller_name: Data controller company name
        controller_address: Controller address
        processor_name: Data processor company name
        processor_address: Processor address
        processing_subject: Subject of data processing
        data_categories: Categories of personal data
        data_subjects: Categories of data subjects
        processing_duration: Duration of processing

    Returns:
        Dictionary with DPA content
    """
    llm = _get_llm()

    dpa_writer = Agent(
        role="DPA Specialist",
        goal="Tworzyć umowy powierzenia przetwarzania danych zgodne z RODO",
        backstory="""Jesteś prawnikiem specjalizującym się w umowach IT i RODO.
        Tworzysz umowy powierzenia przetwarzania danych (DPA) zgodne z Art. 28 RODO.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    data_text = "\n".join(f"- {d}" for d in data_categories)
    subjects_text = "\n".join(f"- {s}" for s in data_subjects)

    task = Task(
        description=f"""
        Stwórz umowę powierzenia przetwarzania danych (DPA) zgodną z Art. 28 RODO:

        ADMINISTRATOR DANYCH:
        - Nazwa: {controller_name}
        - Adres: {controller_address}

        PODMIOT PRZETWARZAJĄCY:
        - Nazwa: {processor_name}
        - Adres: {processor_address}

        PRZEDMIOT PRZETWARZANIA:
        {processing_subject}

        KATEGORIE DANYCH:
        {data_text}

        KATEGORIE OSÓB:
        {subjects_text}

        CZAS PRZETWARZANIA: {processing_duration or "na czas trwania umowy głównej"}

        UMOWA MUSI ZAWIERAĆ (Art. 28 ust. 3 RODO):
        - Przedmiot i czas przetwarzania
        - Charakter i cel przetwarzania
        - Rodzaj danych i kategorie osób
        - Obowiązki i prawa administratora
        - Zobowiązania podmiotu przetwarzającego
        - Zasady podpowierzenia
        - Pomoc w realizacji praw osób
        - Usunięcie danych po zakończeniu
        - Udostępnianie informacji do audytu

        Zwróć w formacie JSON:
        {{
            "title": "Umowa Powierzenia Przetwarzania Danych Osobowych",
            "parties": {{
                "controller": "{controller_name}",
                "processor": "{processor_name}"
            }},
            "sections": [
                {{
                    "number": "§ 1",
                    "title": "tytuł",
                    "content": "treść"
                }}
            ],
            "full_text": "pełna treść umowy",
            "annexes": ["lista wymaganych załączników"]
        }}
        """,
        agent=dpa_writer,
        expected_output="DPA in JSON format",
    )

    crew = Crew(
        agents=[dpa_writer],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    import json
    import re

    result_text = str(result)
    json_match = re.search(r'\{[\s\S]*\}', result_text)

    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return {"success": True, "dpa": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "dpa": {"full_text": result_text}}

"""Terms Generator Agent - Terms of service and policies."""

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


async def generate_terms_of_service(
    company_name: str,
    company_address: str,
    service_type: str,
    service_description: str,
    pricing_model: str = "",
    payment_terms: str = "",
    contact_email: str = "",
    jurisdiction: str = "Polska",
    b2b_only: bool = False,
    subscription_based: bool = False,
    free_trial: bool = False,
    refund_policy: str = "",
) -> dict:
    """Generate Terms of Service document.

    Args:
        company_name: Legal company name
        company_address: Registered address
        service_type: Type of service (SaaS, e-commerce, marketplace, etc.)
        service_description: Description of the service
        pricing_model: How pricing works
        payment_terms: Payment terms and conditions
        contact_email: Contact email
        jurisdiction: Legal jurisdiction
        b2b_only: Whether service is B2B only
        subscription_based: Whether service is subscription based
        free_trial: Whether free trial is offered
        refund_policy: Refund policy description

    Returns:
        Dictionary with Terms of Service content
    """
    llm = _get_llm()

    legal_writer = Agent(
        role="Legal Document Specialist",
        goal="Tworzyć regulaminy zgodne z polskim prawem i UE",
        backstory="""Jesteś prawnikiem specjalizującym się w regulaminach usług
        internetowych. Znasz polskie prawo konsumenckie, ustawę o świadczeniu
        usług drogą elektroniczną i wymogi UE. Piszesz dokumenty, które
        chronią firmę, ale są też zgodne z prawami konsumentów.

        WAŻNE: Dokument ma charakter wzoru i powinien być zweryfikowany
        przez prawnika przed wdrożeniem.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    service_type_info = {
        "saas": "oprogramowanie jako usługa (SaaS)",
        "ecommerce": "sklep internetowy",
        "marketplace": "platforma marketplace",
        "consulting": "usługi doradcze",
        "agency": "usługi agencyjne",
    }

    service_type_pl = service_type_info.get(service_type.lower(), service_type)
    customer_type = "przedsiębiorców (B2B)" if b2b_only else "konsumentów i przedsiębiorców"

    task = Task(
        description=f"""
        Stwórz regulamin świadczenia usług drogą elektroniczną:

        DANE USŁUGODAWCY:
        - Nazwa: {company_name}
        - Adres: {company_address}
        - Email: {contact_email or "[EMAIL]"}

        USŁUGA:
        - Typ: {service_type_pl}
        - Opis: {service_description}
        - Odbiorcy: {customer_type}
        - Model subskrypcyjny: {"Tak" if subscription_based else "Nie"}
        - Darmowy okres próbny: {"Tak" if free_trial else "Nie"}

        PŁATNOŚCI:
        - Model cenowy: {pricing_model or "do uzgodnienia indywidualnie"}
        - Warunki płatności: {payment_terms or "przedpłata"}
        - Polityka zwrotów: {refund_policy or "zgodnie z prawem"}

        JURYSDYKCJA: {jurisdiction}

        REGULAMIN MUSI ZAWIERAĆ:

        1. POSTANOWIENIA OGÓLNE
           - Definicje
           - Dane usługodawcy

        2. WARUNKI KORZYSTANIA Z USŁUGI
           - Rejestracja
           - Wymagania techniczne
           - Zakres usług

        3. PRAWA I OBOWIĄZKI STRON
           - Obowiązki usługodawcy
           - Obowiązki użytkownika
           - Zakazy

        4. PŁATNOŚCI I ROZLICZENIA
           - Cennik
           - Metody płatności
           - Faktury

        5. ODPOWIEDZIALNOŚĆ
           - Ograniczenia odpowiedzialności
           - Siła wyższa

        6. REKLAMACJE
           - Procedura reklamacyjna
           - Terminy

        7. {"ODSTĄPIENIE OD UMOWY (dla konsumentów)" if not b2b_only else "WYPOWIEDZENIE UMOWY"}
           - Prawo odstąpienia
           - Procedura

        8. WŁASNOŚĆ INTELEKTUALNA
           - Prawa autorskie
           - Licencja

        9. OCHRONA DANYCH OSOBOWYCH
           - Odniesienie do polityki prywatności

        10. POSTANOWIENIA KOŃCOWE
            - Zmiany regulaminu
            - Prawo właściwe
            - Rozwiązywanie sporów

        Zwróć w formacie JSON:
        {{
            "title": "Regulamin świadczenia usług",
            "version": "1.0",
            "effective_date": "[DATA]",
            "sections": [
                {{
                    "number": "§ 1",
                    "title": "tytuł sekcji",
                    "content": "treść sekcji"
                }}
            ],
            "full_text": "pełna treść regulaminu",
            "summary_for_users": "krótkie podsumowanie najważniejszych punktów",
            "legal_notices": ["wymagane informacje prawne"],
            "disclaimer": "Dokument wymaga weryfikacji prawnej przed wdrożeniem."
        }}
        """,
        agent=legal_writer,
        expected_output="Terms of Service in JSON format",
    )

    crew = Crew(
        agents=[legal_writer],
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
            return {"success": True, "terms_of_service": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "terms_of_service": {"full_text": result_text}}


async def generate_return_policy(
    company_name: str,
    business_type: str = "ecommerce",
    products_type: str = "",
    return_period_days: int = 14,
    accepts_opened_products: bool = True,
    free_returns: bool = False,
    contact_email: str = "",
) -> dict:
    """Generate a return/refund policy.

    Args:
        company_name: Company name
        business_type: Type of business
        products_type: Type of products sold
        return_period_days: Return period in days
        accepts_opened_products: Whether opened products can be returned
        free_returns: Whether returns are free
        contact_email: Contact email for returns

    Returns:
        Dictionary with return policy content
    """
    llm = _get_llm()

    policy_writer = Agent(
        role="E-commerce Policy Specialist",
        goal="Tworzyć polityki zwrotów zgodne z prawem konsumenckim",
        backstory="""Jesteś specjalistą od polityk e-commerce w Polsce.
        Znasz ustawę o prawach konsumenta i wymogi dotyczące zwrotów.
        Tworzysz polityki, które są zgodne z prawem i przyjazne dla klientów.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""
        Stwórz politykę zwrotów i reklamacji:

        FIRMA: {company_name}
        TYP: {business_type}
        PRODUKTY: {products_type or "różne"}
        OKRES ZWROTU: {return_period_days} dni
        ZWROTY OTWARTYCH: {"Tak" if accepts_opened_products else "Nie"}
        DARMOWE ZWROTY: {"Tak" if free_returns else "Nie"}
        KONTAKT: {contact_email or "[EMAIL]"}

        POLITYKA MUSI ZAWIERAĆ:

        1. PRAWO DO ODSTĄPIENIA (14 dni zgodnie z prawem)
        2. PROCEDURA ZWROTU
        3. STAN PRODUKTU
        4. KOSZTY ZWROTU
        5. CZAS NA ZWROT PIENIĘDZY
        6. REKLAMACJE (rękojmia)
        7. WYJĄTKI (produkty niepodlegające zwrotowi)
        8. KONTAKT

        Zwróć w formacie JSON:
        {{
            "title": "Polityka zwrotów i reklamacji",
            "sections": [
                {{
                    "title": "tytuł",
                    "content": "treść"
                }}
            ],
            "full_text": "pełna treść",
            "quick_facts": [
                {{"fact": "fakt", "value": "wartość"}}
            ],
            "return_form_fields": ["pola formularza zwrotu"]
        }}
        """,
        agent=policy_writer,
        expected_output="Return policy in JSON format",
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
            return {"success": True, "return_policy": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "return_policy": {"full_text": result_text}}

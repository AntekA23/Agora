"""Contract Reviewer Agent - Analyzing contracts and identifying risks."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,  # Low temperature for more precise legal analysis
        api_key=settings.OPENAI_API_KEY,
    )


async def review_contract(
    contract_text: str,
    contract_type: str = "general",
    your_role: str = "buyer",
    key_concerns: list[str] | None = None,
    industry: str = "",
) -> dict:
    """Review a contract and identify risks and issues.

    Args:
        contract_text: The contract text to review
        contract_type: Type of contract (service, employment, nda, lease, etc.)
        your_role: Your role in the contract (buyer, seller, employee, etc.)
        key_concerns: Specific areas to focus on
        industry: Industry context

    Returns:
        Dictionary with contract analysis
    """
    llm = _get_llm()

    legal_analyst = Agent(
        role="Contract Analyst",
        goal="Identyfikować ryzyka i problemy w umowach oraz sugerować poprawki",
        backstory="""Jesteś doświadczonym prawnikiem specjalizującym się w prawie
        umów w Polsce. Masz 15 lat doświadczenia w analizie umów B2B.
        Znasz Kodeks Cywilny, prawo pracy i regulacje branżowe.
        Identyfikujesz klauzule niekorzystne i sugerujesz alternatywy.

        WAŻNE: Podkreślasz, że analiza ma charakter informacyjny i nie
        zastępuje porady prawnej od licencjonowanego prawnika.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    concerns_text = "\n".join(f"- {c}" for c in (key_concerns or []))

    contract_types_map = {
        "general": "umowa ogólna",
        "service": "umowa o świadczenie usług",
        "employment": "umowa o pracę",
        "b2b": "umowa B2B / współpraca",
        "nda": "umowa o zachowaniu poufności (NDA)",
        "lease": "umowa najmu",
        "sale": "umowa sprzedaży",
        "license": "umowa licencyjna",
    }

    contract_type_pl = contract_types_map.get(contract_type, contract_type)

    task = Task(
        description=f"""
        Przeanalizuj poniższą umowę:

        TYP UMOWY: {contract_type_pl}
        TWOJA ROLA: {your_role}
        BRANŻA: {industry or "ogólna"}

        SZCZEGÓLNE OBSZARY ZAINTERESOWANIA:
        {concerns_text or "Brak szczególnych wymagań"}

        TREŚĆ UMOWY:
        ---
        {contract_text[:15000]}  # Limit for context
        ---

        PRZEPROWADŹ ANALIZĘ:

        1. PODSUMOWANIE UMOWY
           - Strony umowy
           - Przedmiot umowy
           - Kluczowe warunki

        2. ANALIZA RYZYK
           - Klauzule niekorzystne dla Ciebie
           - Brakujące zabezpieczenia
           - Niejasne sformułowania

        3. KLAUZULE KRYTYCZNE
           - Odpowiedzialność i odszkodowania
           - Kary umowne
           - Wypowiedzenie
           - Poufność
           - Własność intelektualna

        4. ZGODNOŚĆ Z PRAWEM
           - Potencjalne problemy prawne
           - Klauzule niedozwolone (jeśli dotyczy)

        5. REKOMENDACJE
           - Co zmienić
           - Co dodać
           - Na co zwrócić uwagę

        Zwróć w formacie JSON:
        {{
            "contract_type": "{contract_type_pl}",
            "summary": {{
                "parties": ["strony umowy"],
                "subject": "przedmiot umowy",
                "duration": "czas trwania",
                "value": "wartość (jeśli podana)"
            }},
            "risk_assessment": {{
                "overall_risk": "low/medium/high",
                "risk_score": 1-10,
                "recommendation": "sign/negotiate/reject"
            }},
            "risks": [
                {{
                    "clause": "nazwa/numer klauzuli",
                    "original_text": "oryginalny tekst",
                    "risk_level": "low/medium/high",
                    "issue": "na czym polega problem",
                    "suggested_change": "sugerowana zmiana"
                }}
            ],
            "missing_clauses": [
                {{
                    "clause": "brakująca klauzula",
                    "importance": "critical/important/nice_to_have",
                    "suggested_text": "sugerowana treść"
                }}
            ],
            "positive_aspects": ["korzystne elementy umowy"],
            "legal_concerns": [
                {{
                    "concern": "opis problemu",
                    "legal_basis": "podstawa prawna",
                    "recommendation": "co zrobić"
                }}
            ],
            "negotiation_priorities": [
                {{
                    "priority": 1-5,
                    "item": "co negocjować",
                    "reasoning": "dlaczego"
                }}
            ],
            "disclaimer": "Analiza ma charakter informacyjny i nie stanowi porady prawnej."
        }}
        """,
        agent=legal_analyst,
        expected_output="Contract analysis in JSON format",
    )

    crew = Crew(
        agents=[legal_analyst],
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
            return {
                "success": True,
                "analysis": parsed,
                "contract_type": contract_type,
            }
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "analysis": {"raw_content": result_text},
        "contract_type": contract_type,
    }


async def compare_contracts(
    contract_a: str,
    contract_b: str,
    contract_type: str = "general",
) -> dict:
    """Compare two versions of a contract.

    Args:
        contract_a: First contract version (e.g., original)
        contract_b: Second contract version (e.g., proposed changes)
        contract_type: Type of contract

    Returns:
        Dictionary with comparison results
    """
    llm = _get_llm()

    comparator = Agent(
        role="Contract Comparison Specialist",
        goal="Porównywać wersje umów i identyfikować różnice",
        backstory="""Jesteś specjalistą od analizy porównawczej umów.
        Potrafisz szybko zidentyfikować zmiany między wersjami
        i ocenić ich wpływ na strony umowy.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""
        Porównaj dwie wersje umowy:

        WERSJA A (oryginalna/poprzednia):
        ---
        {contract_a[:8000]}
        ---

        WERSJA B (nowa/proponowana):
        ---
        {contract_b[:8000]}
        ---

        ZIDENTYFIKUJ:
        1. Dodane klauzule
        2. Usunięte klauzule
        3. Zmienione klauzule
        4. Wpływ zmian na każdą ze stron

        Zwróć w formacie JSON:
        {{
            "summary": "podsumowanie zmian",
            "changes": [
                {{
                    "type": "added/removed/modified",
                    "clause": "nazwa klauzuli",
                    "version_a": "tekst w wersji A (lub null)",
                    "version_b": "tekst w wersji B (lub null)",
                    "impact": "wpływ zmiany",
                    "benefits_party": "która strona korzysta"
                }}
            ],
            "overall_impact": {{
                "party_a": "korzystne/niekorzystne/neutralne",
                "party_b": "korzystne/niekorzystne/neutralne"
            }},
            "recommendation": "czy akceptować zmiany"
        }}
        """,
        agent=comparator,
        expected_output="Contract comparison in JSON format",
    )

    crew = Crew(
        agents=[comparator],
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
            return {"success": True, "comparison": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "comparison": {"raw_content": result_text}}

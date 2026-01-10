"""Contract Reviewer Agent - Analyzing contracts under Polish law.

This module provides contract analysis specifically for Polish legal context:
- Kodeks cywilny (Civil Code) compliance
- Kodeks pracy (Labor Code) for employment contracts
- Ustawa o prawach konsumenta (Consumer Rights Act)
- Rejestr klauzul niedozwolonych UOKiK (prohibited clauses registry)
- Polish contract formalities and requirements
"""

import json
import re
from typing import Any

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


# =============================================================================
# POLISH LEGAL REFERENCES
# =============================================================================

POLISH_LEGAL_BASES = {
    "kodeks_cywilny": {
        "name": "Kodeks cywilny",
        "short": "KC",
        "key_articles": {
            "umowy": "Art. 353-396 KC - Zobowiązania umowne",
            "wadliwość": "Art. 58 KC - Nieważność czynności prawnej",
            "klauzule_abuzywne": "Art. 385¹-385³ KC - Niedozwolone postanowienia umowne",
            "kary_umowne": "Art. 483-485 KC - Kary umowne",
            "odstąpienie": "Art. 491-496 KC - Odstąpienie od umowy",
            "przedawnienie": "Art. 117-125 KC - Przedawnienie roszczeń",
            "odsetki": "Art. 359-360 KC - Odsetki",
            "rękojmia": "Art. 556-576 KC - Rękojmia za wady",
            "zlecenie": "Art. 734-751 KC - Umowa zlecenia",
            "dzieło": "Art. 627-646 KC - Umowa o dzieło",
            "najem": "Art. 659-692 KC - Najem",
        },
    },
    "kodeks_pracy": {
        "name": "Kodeks pracy",
        "short": "KP",
        "key_articles": {
            "umowa_o_pracę": "Art. 25-67 KP - Umowa o pracę",
            "wypowiedzenie": "Art. 30-43 KP - Rozwiązanie umowy",
            "zakaz_konkurencji": "Art. 101¹-101⁴ KP - Zakaz konkurencji",
            "wynagrodzenie": "Art. 78-93 KP - Wynagrodzenie",
            "czas_pracy": "Art. 128-151 KP - Czas pracy",
            "urlopy": "Art. 152-175 KP - Urlopy",
        },
    },
    "prawo_konsumenckie": {
        "name": "Ustawa o prawach konsumenta",
        "short": "UPK",
        "key_articles": {
            "odstąpienie_14dni": "Art. 27 UPK - Prawo odstąpienia 14 dni",
            "obowiązki_informacyjne": "Art. 12 UPK - Obowiązki informacyjne",
            "wyjątki_odstąpienia": "Art. 38 UPK - Wyjątki od prawa odstąpienia",
        },
    },
    "usługi_elektroniczne": {
        "name": "Ustawa o świadczeniu usług drogą elektroniczną",
        "short": "UŚUDE",
        "key_articles": {
            "regulamin": "Art. 8 UŚUDE - Regulamin",
            "obowiązki": "Art. 5-7 UŚUDE - Obowiązki usługodawcy",
        },
    },
}

# Najczęstsze klauzule abuzywne z rejestru UOKiK
COMMON_ABUSIVE_CLAUSES = [
    {
        "type": "jednostronna_zmiana",
        "description": "Zastrzeganie prawa do jednostronnej zmiany umowy bez ważnej przyczyny",
        "legal_basis": "Art. 385³ pkt 10 KC",
    },
    {
        "type": "wyłączenie_odpowiedzialności",
        "description": "Wyłączenie odpowiedzialności za niewykonanie zobowiązania",
        "legal_basis": "Art. 385³ pkt 2 KC",
    },
    {
        "type": "kara_bez_wzajemności",
        "description": "Kara umowna tylko dla jednej strony",
        "legal_basis": "Art. 385³ pkt 16 KC",
    },
    {
        "type": "automatyczne_przedłużenie",
        "description": "Automatyczne przedłużenie umowy bez wyraźnej zgody",
        "legal_basis": "Art. 385³ pkt 18 KC",
    },
    {
        "type": "arbitraż_narzucony",
        "description": "Narzucenie sądu polubownego bez zgody konsumenta",
        "legal_basis": "Art. 385³ pkt 23 KC",
    },
    {
        "type": "krótki_termin_reklamacji",
        "description": "Skrócenie terminu na złożenie reklamacji poniżej ustawowego",
        "legal_basis": "Art. 385³ pkt 2 KC",
    },
]

# Terminy przedawnienia wg polskiego prawa
STATUTE_OF_LIMITATIONS = {
    "ogólny": {"okres": "6 lat", "podstawa": "Art. 118 KC"},
    "świadczenia_okresowe": {"okres": "3 lata", "podstawa": "Art. 118 KC"},
    "działalność_gospodarcza": {"okres": "3 lata", "podstawa": "Art. 118 KC"},
    "roszczenia_pracownicze": {"okres": "3 lata", "podstawa": "Art. 291 KP"},
    "rękojmia": {"okres": "2 lata", "podstawa": "Art. 568 KC"},
    "umowa_przewozu": {"okres": "1 rok", "podstawa": "Art. 778 KC"},
}


def _get_llm():
    """Get LLM instance for legal analysis."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,  # Very low for precise legal analysis
        api_key=settings.OPENAI_API_KEY,
    )


def _build_legal_context(contract_type: str) -> str:
    """Build Polish legal context based on contract type."""
    context_parts = []

    # Always include KC
    kc = POLISH_LEGAL_BASES["kodeks_cywilny"]
    context_parts.append(f"\n{kc['name']} ({kc['short']}):")
    for key, desc in kc["key_articles"].items():
        context_parts.append(f"  - {desc}")

    # Add specific laws based on contract type
    if contract_type in ["employment", "praca", "b2b"]:
        kp = POLISH_LEGAL_BASES["kodeks_pracy"]
        context_parts.append(f"\n{kp['name']} ({kp['short']}):")
        for key, desc in kp["key_articles"].items():
            context_parts.append(f"  - {desc}")

    if contract_type in ["service", "saas", "ecommerce", "b2c"]:
        upk = POLISH_LEGAL_BASES["prawo_konsumenckie"]
        context_parts.append(f"\n{upk['name']} ({upk['short']}):")
        for key, desc in upk["key_articles"].items():
            context_parts.append(f"  - {desc}")

    return "\n".join(context_parts)


def _build_abusive_clauses_context() -> str:
    """Build context about common abusive clauses."""
    lines = ["KLAUZULE NIEDOZWOLONE (Art. 385¹-385³ KC + Rejestr UOKiK):"]
    for clause in COMMON_ABUSIVE_CLAUSES:
        lines.append(f"  - {clause['description']} ({clause['legal_basis']})")
    return "\n".join(lines)


async def review_contract(
    contract_text: str,
    contract_type: str = "general",
    your_role: str = "buyer",
    key_concerns: list[str] | None = None,
    industry: str = "",
    is_b2c: bool = False,
) -> dict[str, Any]:
    """Review a contract under Polish law.

    Args:
        contract_text: The contract text to review
        contract_type: Type of contract:
            - general: umowa ogólna
            - service: umowa o świadczenie usług
            - employment: umowa o pracę
            - b2b: umowa B2B / współpraca
            - zlecenie: umowa zlecenia
            - dzielo: umowa o dzieło
            - nda: umowa o zachowaniu poufności
            - lease: umowa najmu
            - sale: umowa sprzedaży
            - license: umowa licencyjna
            - saas: umowa SaaS
        your_role: Your role (buyer, seller, employee, employer, etc.)
        key_concerns: Specific areas to focus on
        industry: Industry context
        is_b2c: Whether this is a B2C contract (enables consumer protection checks)

    Returns:
        Dictionary with contract analysis including Polish legal references
    """
    llm = _get_llm()

    # Build legal context
    legal_context = _build_legal_context(contract_type)
    abusive_context = _build_abusive_clauses_context() if is_b2c else ""

    contract_types_map = {
        "general": "umowa ogólna",
        "service": "umowa o świadczenie usług",
        "employment": "umowa o pracę",
        "b2b": "umowa B2B / współpraca",
        "zlecenie": "umowa zlecenia",
        "dzielo": "umowa o dzieło",
        "nda": "umowa o zachowaniu poufności (NDA)",
        "lease": "umowa najmu",
        "sale": "umowa sprzedaży",
        "license": "umowa licencyjna",
        "saas": "umowa SaaS",
    }
    contract_type_pl = contract_types_map.get(contract_type, contract_type)

    concerns_text = "\n".join(f"- {c}" for c in (key_concerns or []))

    # Prepare conditional sections for the prompt (avoid backslash in f-strings)
    b2c_check_text = "Czy są klauzule niedozwolone? (Art. 385¹-385³ KC)" if is_b2c else ""
    b2c_withdrawal_text = "Prawo odstąpienia 14 dni (Art. 27 UPK)" if is_b2c else ""

    abusive_clauses_section = ""
    if is_b2c:
        abusive_clauses_section = '''
            "abusive_clauses": [
                {
                    "clause_text": "tekst klauzuli",
                    "why_abusive": "dlaczego niedozwolona",
                    "legal_basis": "Art. 385³ pkt X KC",
                    "similar_uokik": "podobna klauzula z rejestru UOKiK (jeśli jest)"
                }
            ],'''

    legal_analyst = Agent(
        role="Polski Prawnik - Specjalista od Umów",
        goal="Analizować umowy pod kątem zgodności z polskim prawem i identyfikować ryzyka",
        backstory=f"""Jesteś doświadczonym polskim radcą prawnym z 15-letnim doświadczeniem
        w prawie umów. Specjalizujesz się w:
        - Kodeksie cywilnym (zobowiązania, umowy)
        - Kodeksie pracy (umowy o pracę, B2B)
        - Prawie konsumenckim (ochrona konsumentów, klauzule abuzywne)
        - Rejestrze klauzul niedozwolonych UOKiK

        Zawsze podajesz konkretne podstawy prawne (artykuły ustaw).

        PODSTAWY PRAWNE DO WYKORZYSTANIA:
        {legal_context}

        {abusive_context}

        TERMINY PRZEDAWNIENIA:
        - Roszczenia ogólne: 6 lat (Art. 118 KC)
        - Działalność gospodarcza: 3 lata (Art. 118 KC)
        - Roszczenia pracownicze: 3 lata (Art. 291 KP)
        - Rękojmia: 2 lata (Art. 568 KC)

        WAŻNE: Twoja analiza ma charakter informacyjny i nie zastępuje porady prawnej
        od radcy prawnego lub adwokata.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""
        Przeanalizuj poniższą umowę zgodnie z polskim prawem:

        TYP UMOWY: {contract_type_pl}
        TWOJA ROLA: {your_role}
        BRANŻA: {industry or "ogólna"}
        UMOWA B2C (ochrona konsumenta): {"TAK - sprawdź klauzule abuzywne!" if is_b2c else "NIE"}

        SZCZEGÓLNE OBSZARY ZAINTERESOWANIA:
        {concerns_text or "Brak szczególnych wymagań"}

        TREŚĆ UMOWY:
        ---
        {contract_text[:15000]}
        ---

        PRZEPROWADŹ ANALIZĘ ZGODNIE Z POLSKIM PRAWEM:

        1. PODSUMOWANIE UMOWY
           - Strony umowy (czy prawidłowo oznaczone?)
           - Przedmiot umowy
           - Kluczowe warunki
           - Forma umowy (czy wymagana forma szczególna?)

        2. ZGODNOŚĆ Z POLSKIM PRAWEM
           - Czy umowa spełnia wymogi formalne?
           - Czy są klauzule sprzeczne z ustawą? (Art. 58 KC)
           - {b2c_check_text}

        3. ANALIZA KLUCZOWYCH POSTANOWIEŃ
           - Wynagrodzenie/cena (czy określone prawidłowo?)
           - Terminy (czy realistyczne i zgodne z ustawą?)
           - Odpowiedzialność (czy nie jest nadmiernie ograniczona?)
           - Kary umowne (czy proporcjonalne? Art. 484 KC)
           - Wypowiedzenie (czy zgodne z ustawowymi terminami?)

        4. ANALIZA RYZYK
           - Klauzule niekorzystne dla Ciebie
           - Brakujące zabezpieczenia
           - Niejasne sformułowania

        5. TERMINY USTAWOWE DO SPRAWDZENIA
           - Przedawnienie roszczeń
           - Terminy wypowiedzenia
           - {b2c_withdrawal_text}

        6. REKOMENDACJE
           - Co zmienić (z podstawą prawną)
           - Co dodać
           - Priorytety negocjacyjne

        Zwróć w formacie JSON:
        {{
            "contract_type": "{contract_type_pl}",
            "summary": {{
                "parties": ["strony umowy"],
                "subject": "przedmiot umowy",
                "duration": "czas trwania",
                "value": "wartość (jeśli podana)",
                "form_requirements": "wymagania co do formy"
            }},
            "legal_compliance": {{
                "is_valid": true/false,
                "formal_requirements_met": true/false,
                "issues": [
                    {{
                        "issue": "opis problemu",
                        "legal_basis": "podstawa prawna (np. Art. 58 KC)",
                        "severity": "critical/high/medium/low",
                        "consequence": "skutek prawny"
                    }}
                ]
            }},
            {abusive_clauses_section}
            "risk_assessment": {{
                "overall_risk": "low/medium/high",
                "risk_score": 1-10,
                "recommendation": "sign/negotiate/reject/consult_lawyer"
            }},
            "clause_analysis": [
                {{
                    "clause_name": "nazwa klauzuli",
                    "original_text": "oryginalny tekst",
                    "legal_assessment": "ocena prawna",
                    "legal_basis": "podstawa prawna",
                    "risk_level": "low/medium/high",
                    "suggested_change": "sugerowana zmiana"
                }}
            ],
            "missing_clauses": [
                {{
                    "clause": "brakująca klauzula",
                    "legal_basis": "dlaczego wymagana",
                    "importance": "critical/important/recommended",
                    "suggested_text": "sugerowana treść"
                }}
            ],
            "statute_of_limitations": {{
                "applicable_period": "okres przedawnienia",
                "legal_basis": "podstawa prawna",
                "notes": "uwagi"
            }},
            "negotiation_priorities": [
                {{
                    "priority": 1,
                    "item": "co negocjować",
                    "legal_argument": "argument prawny",
                    "fallback_position": "pozycja awaryjna"
                }}
            ],
            "positive_aspects": ["korzystne elementy umowy"],
            "lawyer_consultation_needed": true/false,
            "disclaimer": "Analiza ma charakter informacyjny i nie stanowi porady prawnej. W przypadku wątpliwości skonsultuj się z radcą prawnym lub adwokatem."
        }}
        """,
        agent=legal_analyst,
        expected_output="Contract analysis in JSON format with Polish legal references",
    )

    crew = Crew(
        agents=[legal_analyst],
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
            return {
                "success": True,
                "analysis": parsed,
                "contract_type": contract_type,
                "is_b2c": is_b2c,
                "legal_system": "polish",
            }
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "analysis": {"raw_content": result_text},
        "contract_type": contract_type,
        "is_b2c": is_b2c,
        "legal_system": "polish",
    }


async def analyze_employment_contract(
    contract_text: str,
    employee_perspective: bool = True,
    contract_subtype: str = "umowa_o_prace",
) -> dict[str, Any]:
    """Specialized analysis for Polish employment contracts.

    Args:
        contract_text: The employment contract text
        employee_perspective: Whether analyzing from employee's perspective
        contract_subtype: Type of employment contract:
            - umowa_o_prace: standard employment contract
            - b2b: B2B cooperation contract
            - zlecenie: civil law contract (zlecenie)
            - dzielo: contract for specific work (dzieło)

    Returns:
        Dictionary with employment contract analysis
    """
    llm = _get_llm()

    subtype_info = {
        "umowa_o_prace": {
            "name": "Umowa o pracę",
            "law": "Kodeks pracy",
            "protections": "Pełna ochrona pracownicza (urlop, L4, wypowiedzenie)",
        },
        "b2b": {
            "name": "Umowa B2B",
            "law": "Kodeks cywilny (zlecenie/usługi)",
            "protections": "Brak ochrony pracowniczej, ale elastyczność",
        },
        "zlecenie": {
            "name": "Umowa zlecenia",
            "law": "Art. 734-751 Kodeksu cywilnego",
            "protections": "Minimalne (składki ZUS, minimalna stawka)",
        },
        "dzielo": {
            "name": "Umowa o dzieło",
            "law": "Art. 627-646 Kodeksu cywilnego",
            "protections": "Brak (brak ZUS, brak minimalnej stawki)",
        },
    }

    info = subtype_info.get(contract_subtype, subtype_info["umowa_o_prace"])
    perspective = "pracownika" if employee_perspective else "pracodawcy"

    employment_expert = Agent(
        role="Specjalista Prawa Pracy",
        goal="Analizować umowy zatrudnienia pod kątem zgodności z polskim prawem pracy",
        backstory=f"""Jesteś specjalistą prawa pracy z 10-letnim doświadczeniem.
        Znasz szczegółowo:
        - Kodeks pracy (wszystkie rodzaje umów o pracę)
        - Umowy cywilnoprawne (zlecenie, dzieło, B2B)
        - Orzecznictwo SN dotyczące stosunku pracy
        - Różnice między umową o pracę a B2B (pozorne samozatrudnienie)

        KLUCZOWE PRZEPISY:
        - Art. 22 KP - Definicja stosunku pracy
        - Art. 25-67 KP - Umowa o pracę
        - Art. 29 KP - Obowiązkowe elementy umowy
        - Art. 30-43 KP - Rozwiązanie umowy
        - Art. 36 KP - Okresy wypowiedzenia
        - Art. 52 KP - Zwolnienie dyscyplinarne
        - Art. 101¹-101⁴ KP - Zakaz konkurencji

        MINIMALNE WYNAGRODZENIE 2024: 4242 PLN brutto / 27,70 PLN/godz.

        Analizujesz z perspektywy: {perspective}""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""
        Przeanalizuj umowę zatrudnienia:

        TYP UMOWY: {info['name']}
        PODSTAWA PRAWNA: {info['law']}
        OCHRONA: {info['protections']}
        PERSPEKTYWA: {perspective}

        TREŚĆ UMOWY:
        ---
        {contract_text[:12000]}
        ---

        SPRAWDŹ:

        1. KWALIFIKACJA UMOWY
           - Czy właściwy typ umowy? (Art. 22 KP - cechy stosunku pracy)
           - Czy nie ma cech "ukrytej umowy o pracę"?
           - Ryzyko przekwalifikowania przez ZUS/PIP

        2. OBOWIĄZKOWE ELEMENTY (Art. 29 KP dla umowy o pracę)
           - Strony umowy
           - Rodzaj pracy
           - Miejsce wykonywania
           - Wynagrodzenie
           - Wymiar czasu pracy
           - Termin rozpoczęcia

        3. WYNAGRODZENIE
           - Czy powyżej minimum? (4242 PLN brutto)
           - Składniki wynagrodzenia
           - Premie i dodatki

        4. CZAS PRACY
           - Wymiar (pełny/część etatu)
           - Nadgodziny
           - Praca zdalna

        5. ROZWIĄZANIE UMOWY
           - Okresy wypowiedzenia (Art. 36 KP)
           - Przyczyny wypowiedzenia
           - Zakaz konkurencji po ustaniu

        6. ZAKAZ KONKURENCJI
           - Czy jest i czy ważny?
           - Odszkodowanie (min. 25% wynagrodzenia - Art. 101² KP)
           - Zakres i czas trwania

        Zwróć w formacie JSON:
        {{
            "contract_type": {{
                "declared": "{info['name']}",
                "actual_assessment": "faktyczny charakter umowy",
                "reclassification_risk": "low/medium/high",
                "reclassification_reasons": ["powody ryzyka"]
            }},
            "mandatory_elements": {{
                "all_present": true/false,
                "missing": ["brakujące elementy"],
                "issues": ["problemy"]
            }},
            "compensation": {{
                "base_salary": "kwota",
                "meets_minimum": true/false,
                "bonuses": ["premie"],
                "issues": ["problemy z wynagrodzeniem"]
            }},
            "working_time": {{
                "type": "pełny etat/część etatu/zadaniowy",
                "overtime_rules": "zasady nadgodzin",
                "issues": ["problemy"]
            }},
            "termination": {{
                "notice_periods": {{
                    "employee": "okres dla pracownika",
                    "employer": "okres dla pracodawcy",
                    "legal_minimum": "minimum ustawowe"
                }},
                "immediate_termination_clauses": ["klauzule natychmiastowego rozwiązania"],
                "issues": ["problemy"]
            }},
            "non_compete": {{
                "exists": true/false,
                "during_employment": {{
                    "valid": true/false,
                    "scope": "zakres"
                }},
                "after_employment": {{
                    "valid": true/false,
                    "duration": "czas trwania",
                    "compensation": "odszkodowanie",
                    "compensation_adequate": true/false,
                    "issues": ["problemy"]
                }}
            }},
            "risk_assessment": {{
                "overall_risk": "low/medium/high",
                "for_employee": ["ryzyka dla pracownika"],
                "for_employer": ["ryzyka dla pracodawcy"]
            }},
            "recommendations": [
                {{
                    "issue": "problem",
                    "legal_basis": "podstawa prawna",
                    "recommendation": "rekomendacja",
                    "priority": "high/medium/low"
                }}
            ],
            "disclaimer": "Analiza informacyjna. W sprawach pracowniczych skonsultuj się z prawnikiem lub PIP."
        }}
        """,
        agent=employment_expert,
        expected_output="Employment contract analysis in JSON format",
    )

    crew = Crew(
        agents=[employment_expert],
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
            return {
                "success": True,
                "analysis": parsed,
                "contract_subtype": contract_subtype,
                "perspective": "employee" if employee_perspective else "employer",
            }
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "analysis": {"raw_content": result_text},
        "contract_subtype": contract_subtype,
    }


async def compare_contracts(
    contract_a: str,
    contract_b: str,
    contract_type: str = "general",
) -> dict[str, Any]:
    """Compare two versions of a contract under Polish law.

    Args:
        contract_a: First contract version (e.g., original)
        contract_b: Second contract version (e.g., proposed changes)
        contract_type: Type of contract

    Returns:
        Dictionary with comparison results
    """
    llm = _get_llm()

    comparator = Agent(
        role="Specjalista ds. Porównywania Umów",
        goal="Porównywać wersje umów i oceniać wpływ zmian zgodnie z polskim prawem",
        backstory="""Jesteś specjalistą od analizy porównawczej umów w Polsce.
        Potrafisz szybko zidentyfikować zmiany między wersjami
        i ocenić ich wpływ prawny na strony umowy.
        Zawsze podajesz podstawy prawne dla ocen.""",
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
        5. Zgodność zmian z polskim prawem

        Zwróć w formacie JSON:
        {{
            "summary": "podsumowanie zmian",
            "total_changes": liczba,
            "changes": [
                {{
                    "type": "added/removed/modified",
                    "clause": "nazwa klauzuli",
                    "version_a": "tekst w wersji A (lub null)",
                    "version_b": "tekst w wersji B (lub null)",
                    "legal_impact": "wpływ prawny zmiany",
                    "legal_basis": "podstawa prawna (jeśli dotyczy)",
                    "benefits_party": "która strona korzysta",
                    "risk_level": "low/medium/high"
                }}
            ],
            "overall_impact": {{
                "party_a": "korzystne/niekorzystne/neutralne",
                "party_b": "korzystne/niekorzystne/neutralne",
                "legal_validity": "czy zmiany są prawnie dopuszczalne"
            }},
            "recommendation": {{
                "accept": true/false,
                "reasoning": "uzasadnienie",
                "negotiation_points": ["punkty do negocjacji"]
            }}
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
    result_text = str(result)

    json_match = re.search(r"\{[\s\S]*\}", result_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return {"success": True, "comparison": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "comparison": {"raw_content": result_text}}


async def check_abusive_clauses(
    contract_text: str,
    contract_type: str = "b2c",
) -> dict[str, Any]:
    """Check contract for abusive clauses under Polish consumer law.

    This is specifically for B2C contracts where consumer protection applies.

    Args:
        contract_text: The contract text to check
        contract_type: Type of contract

    Returns:
        Dictionary with abusive clauses analysis
    """
    llm = _get_llm()

    abusive_clauses_text = "\n".join([
        f"- {c['type']}: {c['description']} ({c['legal_basis']})"
        for c in COMMON_ABUSIVE_CLAUSES
    ])

    consumer_expert = Agent(
        role="Specjalista Prawa Konsumenckiego",
        goal="Identyfikować klauzule niedozwolone w umowach konsumenckich",
        backstory=f"""Jesteś ekspertem od prawa konsumenckiego w Polsce.
        Specjalizujesz się w identyfikacji klauzul abuzywnych zgodnie z:
        - Art. 385¹-385³ Kodeksu cywilnego
        - Rejestrem klauzul niedozwolonych UOKiK
        - Orzecznictwem SOKiK

        TYPOWE KLAUZULE NIEDOZWOLONE:
        {abusive_clauses_text}

        KRYTERIA KLAUZULI NIEDOZWOLONEJ (Art. 385¹ KC):
        1. Nie została uzgodniona indywidualnie
        2. Kształtuje prawa/obowiązki konsumenta sprzecznie z dobrymi obyczajami
        3. Rażąco narusza interesy konsumenta

        SKUTEK: Klauzula nie wiąże konsumenta (Art. 385¹ § 2 KC)""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""
        Sprawdź umowę pod kątem klauzul niedozwolonych:

        TREŚĆ UMOWY:
        ---
        {contract_text[:12000]}
        ---

        DLA KAŻDEJ POTENCJALNEJ KLAUZULI NIEDOZWOLONEJ SPRAWDŹ:
        1. Czy mieści się w katalogu Art. 385³ KC?
        2. Czy jest podobna do klauzul z rejestru UOKiK?
        3. Czy rażąco narusza interesy konsumenta?
        4. Czy została uzgodniona indywidualnie?

        Zwróć w formacie JSON:
        {{
            "abusive_clauses_found": liczba,
            "overall_assessment": "safe/risky/dangerous",
            "clauses": [
                {{
                    "clause_text": "pełny tekst klauzuli",
                    "location": "gdzie w umowie",
                    "type": "typ klauzuli niedozwolonej",
                    "legal_basis": "Art. 385³ pkt X KC",
                    "why_abusive": "dlaczego jest niedozwolona",
                    "similar_uokik_clause": "podobna klauzula z rejestru (jeśli jest)",
                    "severity": "high/medium/low",
                    "consumer_impact": "skutek dla konsumenta",
                    "suggested_alternative": "alternatywne sformułowanie"
                }}
            ],
            "safe_clauses": ["klauzule, które są w porządku"],
            "recommendations": [
                {{
                    "action": "co zrobić",
                    "priority": "high/medium/low"
                }}
            ],
            "legal_consequences": {{
                "for_business": "konsekwencje dla przedsiębiorcy",
                "for_consumer": "prawa konsumenta",
                "uokik_risk": "ryzyko interwencji UOKiK"
            }},
            "disclaimer": "Analiza informacyjna. Ostateczną ocenę może wydać sąd lub UOKiK."
        }}
        """,
        agent=consumer_expert,
        expected_output="Abusive clauses analysis in JSON format",
    )

    crew = Crew(
        agents=[consumer_expert],
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
            return {"success": True, "analysis": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "analysis": {"raw_content": result_text}}

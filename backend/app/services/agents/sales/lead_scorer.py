"""Lead Scoring Agent - Scoring and qualifying leads."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.agents.tools.web_search import search_tool


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,  # Lower temperature for more consistent scoring
        api_key=settings.OPENAI_API_KEY,
    )


async def score_lead(
    company_name: str,
    contact_name: str = "",
    contact_title: str = "",
    company_size: str = "",
    industry: str = "",
    budget: str = "",
    timeline: str = "",
    pain_points: list[str] | None = None,
    interaction_history: list[dict] | None = None,
    source: str = "",
    ideal_customer_profile: dict | None = None,
    use_web_search: bool = True,
) -> dict:
    """Score a sales lead based on multiple criteria.

    Args:
        company_name: Lead company name
        contact_name: Contact person name
        contact_title: Contact's job title
        company_size: Company size (employees or revenue)
        industry: Company industry
        budget: Known or estimated budget
        timeline: Purchase timeline
        pain_points: Identified pain points
        interaction_history: List of past interactions
            [{"date": "...", "type": "...", "notes": "..."}]
        source: Lead source (website, referral, event, etc.)
        ideal_customer_profile: ICP to compare against
        use_web_search: Research company for additional context

    Returns:
        Dictionary with lead score and analysis
    """
    llm = _get_llm()

    tools = [search_tool] if use_web_search and settings.TAVILY_API_KEY else []

    lead_analyst = Agent(
        role="Sales Intelligence Analyst",
        goal="Obiektywnie oceniać i kwalifikować leady sprzedażowe",
        backstory="""Jesteś analitykiem sprzedaży z doświadczeniem w B2B.
        Potrafisz szybko ocenić potencjał leada na podstawie dostępnych danych.
        Stosujesz metodologię BANT (Budget, Authority, Need, Timeline) i
        scoring predykcyjny. Twoje oceny są obiektywne i mierzalne.""",
        tools=tools,
        llm=llm,
        verbose=False,
    )

    pain_points_text = "\n".join(f"- {p}" for p in (pain_points or ["brak danych"]))

    history_text = ""
    if interaction_history:
        for h in interaction_history:
            history_text += f"- {h.get('date', '?')}: {h.get('type', '?')} - {h.get('notes', '')}\n"
    else:
        history_text = "Brak historii interakcji"

    icp_text = ""
    if ideal_customer_profile:
        icp_text = f"""
        IDEALNY PROFIL KLIENTA (ICP):
        - Branża: {ideal_customer_profile.get('industry', 'dowolna')}
        - Wielkość: {ideal_customer_profile.get('size', 'dowolna')}
        - Budżet min: {ideal_customer_profile.get('min_budget', 'brak')}
        - Stanowiska decyzyjne: {', '.join(ideal_customer_profile.get('decision_makers', []))}
        """

    research_context = ""
    if use_web_search and tools:
        research_context = f"""
        NAJPIERW przeprowadź research firmy {company_name}:
        1. Sprawdź wielkość firmy i przychody
        2. Zidentyfikuj kluczowe osoby decyzyjne
        3. Sprawdź ostatnie aktywności/inwestycje
        4. Oceń kondycję finansową
        """

    task = Task(
        description=f"""
        {research_context}

        Oceń lead sprzedażowy według metodologii BANT i scoring predykcyjny:

        DANE LEADA:
        - Firma: {company_name}
        - Kontakt: {contact_name or "nieznany"}
        - Stanowisko: {contact_title or "nieznane"}
        - Wielkość firmy: {company_size or "nieznana"}
        - Branża: {industry or "nieznana"}
        - Budżet: {budget or "nieznany"}
        - Timeline: {timeline or "nieznany"}
        - Źródło: {source or "nieznane"}

        ZIDENTYFIKOWANE POTRZEBY:
        {pain_points_text}

        HISTORIA INTERAKCJI:
        {history_text}

        {icp_text}

        KRYTERIA SCORINGU:

        1. BUDGET (0-25 pkt)
           - Czy mają budżet?
           - Czy budżet pasuje do naszej oferty?

        2. AUTHORITY (0-25 pkt)
           - Czy kontakt jest decydentem?
           - Czy mamy dostęp do decydentów?

        3. NEED (0-25 pkt)
           - Czy mają realną potrzebę?
           - Czy nasza oferta ją adresuje?

        4. TIMELINE (0-25 pkt)
           - Jak pilna jest potrzeba?
           - Kiedy planują zakup?

        DODATKOWE CZYNNIKI:
        - Dopasowanie do ICP (+/- 10 pkt)
        - Jakość źródła (+/- 5 pkt)
        - Engagement w interakcjach (+/- 5 pkt)

        Zwróć w formacie JSON:
        {{
            "lead": {{
                "company": "{company_name}",
                "contact": "{contact_name}",
                "title": "{contact_title}"
            }},
            "scores": {{
                "budget": {{
                    "score": 0-25,
                    "confidence": "high/medium/low",
                    "reasoning": "uzasadnienie"
                }},
                "authority": {{
                    "score": 0-25,
                    "confidence": "high/medium/low",
                    "reasoning": "uzasadnienie"
                }},
                "need": {{
                    "score": 0-25,
                    "confidence": "high/medium/low",
                    "reasoning": "uzasadnienie"
                }},
                "timeline": {{
                    "score": 0-25,
                    "confidence": "high/medium/low",
                    "reasoning": "uzasadnienie"
                }},
                "icp_fit": {{
                    "score": -10 to +10,
                    "reasoning": "uzasadnienie"
                }},
                "engagement": {{
                    "score": -5 to +5,
                    "reasoning": "uzasadnienie"
                }}
            }},
            "total_score": 0-100,
            "grade": "A/B/C/D",
            "qualification": "MQL/SQL/Hot Lead/Disqualified",
            "probability_to_close": "X%",
            "recommended_actions": ["kolejne kroki"],
            "risks": ["ryzyka"],
            "missing_information": ["czego brakuje"],
            "summary": "podsumowanie 2-3 zdania"
        }}
        """,
        agent=lead_analyst,
        expected_output="Lead score in JSON format",
    )

    crew = Crew(
        agents=[lead_analyst],
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
                "lead_score": parsed,
                "company": company_name,
            }
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "lead_score": {"raw_analysis": result_text},
        "company": company_name,
    }


async def analyze_leads_batch(
    leads: list[dict],
    ideal_customer_profile: dict | None = None,
) -> dict:
    """Analyze and prioritize multiple leads.

    Args:
        leads: List of lead data dictionaries
        ideal_customer_profile: ICP to compare against

    Returns:
        Dictionary with prioritized leads
    """
    llm = _get_llm()

    prioritizer = Agent(
        role="Sales Prioritization Expert",
        goal="Priorytetyzować leady dla maksymalnej efektywności sprzedaży",
        backstory="""Jesteś ekspertem od priorytetyzacji pipeline'u sprzedażowego.
        Wiesz, że czas handlowca jest cenny i pomagasz skupić się na
        najbardziej obiecujących szansach.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    leads_text = ""
    for i, lead in enumerate(leads, 1):
        leads_text += f"""
        LEAD #{i}:
        - Firma: {lead.get('company_name', 'N/A')}
        - Kontakt: {lead.get('contact_name', 'N/A')}
        - Branża: {lead.get('industry', 'N/A')}
        - Wielkość: {lead.get('company_size', 'N/A')}
        - Budżet: {lead.get('budget', 'N/A')}
        - Timeline: {lead.get('timeline', 'N/A')}
        - Źródło: {lead.get('source', 'N/A')}
        ---"""

    icp_text = ""
    if ideal_customer_profile:
        icp_text = f"ICP: {ideal_customer_profile}"

    task = Task(
        description=f"""
        Przeanalizuj i spriorytetyzuj następujące leady:

        {leads_text}

        {icp_text}

        Zwróć w formacie JSON:
        {{
            "total_leads": {len(leads)},
            "prioritized_leads": [
                {{
                    "rank": 1,
                    "company": "nazwa",
                    "quick_score": 0-100,
                    "priority": "high/medium/low",
                    "reasoning": "dlaczego ta pozycja",
                    "recommended_action": "co zrobić"
                }}
            ],
            "summary": {{
                "hot_leads": liczba,
                "warm_leads": liczba,
                "cold_leads": liczba,
                "disqualified": liczba
            }},
            "recommendations": ["ogólne rekomendacje"]
        }}
        """,
        agent=prioritizer,
        expected_output="Prioritized leads in JSON format",
    )

    crew = Crew(
        agents=[prioritizer],
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
            return {"success": True, "analysis": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "analysis": {"raw_result": result_text}}

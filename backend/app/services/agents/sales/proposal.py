"""Sales Proposal Generator Agent."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.agents.tools.web_search import search_tool


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY,
    )


async def generate_sales_proposal(
    client_name: str,
    client_industry: str,
    client_needs: list[str],
    products_services: list[dict],
    company_name: str = "",
    company_description: str = "",
    proposal_type: str = "standard",
    budget_range: str = "",
    timeline: str = "",
    competitive_advantages: list[str] | None = None,
    use_web_search: bool = True,
) -> dict:
    """Generate a professional sales proposal.

    Args:
        client_name: Client company name
        client_industry: Client's industry
        client_needs: List of client's identified needs/pain points
        products_services: List of products/services to propose
            [{"name": "...", "description": "...", "price": "...", "benefits": [...]}]
        company_name: Your company name
        company_description: Your company description
        proposal_type: standard, enterprise, startup
        budget_range: Client's budget range if known
        timeline: Project timeline
        competitive_advantages: Your advantages over competition
        use_web_search: Research client and industry

    Returns:
        Dictionary with proposal content
    """
    llm = _get_llm()

    tools = [search_tool] if use_web_search and settings.TAVILY_API_KEY else []

    proposal_writer = Agent(
        role="Senior Sales Consultant",
        goal="Tworzyć przekonujące oferty handlowe, które wygrywają kontrakty",
        backstory="""Jesteś doświadczonym konsultantem sprzedaży B2B z 15-letnim stażem.
        Napisałeś setki zwycięskich ofert dla polskich firm.
        Wiesz jak pokazać wartość rozwiązania, nie tylko cenę.
        Znasz techniki perswazji i storytellingu w sprzedaży.
        Piszesz profesjonalnie po polsku.""",
        tools=tools,
        llm=llm,
        verbose=False,
    )

    needs_text = "\n".join(f"- {n}" for n in client_needs)
    advantages_text = "\n".join(f"- {a}" for a in (competitive_advantages or []))

    products_text = ""
    for p in products_services:
        products_text += f"""
        Produkt/Usługa: {p.get('name', 'N/A')}
        Opis: {p.get('description', '')}
        Cena: {p.get('price', 'do uzgodnienia')}
        Korzyści: {', '.join(p.get('benefits', []))}
        ---"""

    research_context = ""
    if use_web_search and tools:
        research_context = f"""
        NAJPIERW przeprowadź research:
        1. Sprawdź informacje o firmie {client_name}
        2. Poznaj specyfikę branży {client_industry} w Polsce
        3. Zidentyfikuj typowe wyzwania w tej branży
        4. Sprawdź jakie rozwiązania stosuje konkurencja
        """

    task = Task(
        description=f"""
        {research_context}

        Stwórz profesjonalną ofertę handlową:

        DANE KLIENTA:
        - Firma: {client_name}
        - Branża: {client_industry}
        - Budżet: {budget_range or "nie określony"}
        - Timeline: {timeline or "do uzgodnienia"}

        POTRZEBY KLIENTA:
        {needs_text}

        NASZA FIRMA:
        {company_name or "[Nazwa firmy]"}
        {company_description}

        NASZE PRZEWAGI:
        {advantages_text or "Jakość, doświadczenie, wsparcie"}

        OFEROWANE ROZWIĄZANIA:
        {products_text}

        TYP OFERTY: {proposal_type}

        STRUKTURA OFERTY:

        1. STRESZCZENIE WYKONAWCZE
           - Krótkie podsumowanie oferty
           - Kluczowe korzyści dla klienta

        2. ZROZUMIENIE POTRZEB
           - Pokazanie, że rozumiesz klienta
           - Diagnoza sytuacji

        3. PROPONOWANE ROZWIĄZANIE
           - Szczegółowy opis
           - Jak adresuje potrzeby klienta
           - Dlaczego to najlepsze rozwiązanie

        4. METODOLOGIA / PROCES
           - Jak będzie wyglądała współpraca
           - Kamienie milowe
           - Timeline

        5. ZESPÓŁ / DOŚWIADCZENIE
           - Dlaczego my
           - Referencje / case studies

        6. CENNIK
           - Przejrzysta wycena
           - Opcje pakietów
           - Warunki płatności

        7. NASTĘPNE KROKI
           - CTA
           - Kontakt

        Zwróć w formacie JSON:
        {{
            "client": "{client_name}",
            "proposal_title": "tytuł oferty",
            "executive_summary": "streszczenie 3-4 zdania",
            "sections": [
                {{
                    "title": "tytuł sekcji",
                    "content": "treść sekcji"
                }}
            ],
            "pricing": {{
                "packages": [
                    {{
                        "name": "nazwa pakietu",
                        "price": "cena",
                        "includes": ["co zawiera"],
                        "recommended": true/false
                    }}
                ],
                "payment_terms": "warunki płatności",
                "validity": "ważność oferty"
            }},
            "timeline": {{
                "total_duration": "czas trwania",
                "milestones": [
                    {{"phase": "faza", "duration": "czas", "deliverables": ["rezultaty"]}}
                ]
            }},
            "next_steps": ["kolejne kroki"],
            "contact": {{
                "cta": "zachęta do kontaktu",
                "deadline": "termin odpowiedzi"
            }},
            "full_text": "pełna treść oferty jako tekst"
        }}
        """,
        agent=proposal_writer,
        expected_output="Sales proposal in JSON format",
    )

    crew = Crew(
        agents=[proposal_writer],
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
                "proposal": parsed,
                "client": client_name,
                "proposal_type": proposal_type,
            }
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "proposal": {"full_text": result_text},
        "client": client_name,
        "proposal_type": proposal_type,
    }

"""Ticket Handler Agent - Handling support tickets."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.5,
        api_key=settings.OPENAI_API_KEY,
    )


async def handle_ticket(
    ticket_subject: str,
    ticket_content: str,
    customer_name: str = "",
    customer_history: list[dict] | None = None,
    product_context: str = "",
    company_name: str = "",
    tone: str = "professional",
    include_next_steps: bool = True,
) -> dict:
    """Handle a support ticket and generate a response.

    Args:
        ticket_subject: Ticket subject line
        ticket_content: Full ticket content
        customer_name: Customer name for personalization
        customer_history: Previous interactions with customer
        product_context: Context about the product/service
        company_name: Company name
        tone: Response tone (professional, friendly, formal)
        include_next_steps: Include next steps in response

    Returns:
        Dictionary with ticket analysis and suggested response
    """
    llm = _get_llm()

    support_agent = Agent(
        role="Customer Support Specialist",
        goal="Profesjonalnie i empatycznie odpowiadać na zgłoszenia klientów",
        backstory="""Jesteś doświadczonym specjalistą obsługi klienta.
        Rozumiesz frustracje klientów i potrafisz przekształcić negatywne
        doświadczenia w pozytywne. Piszesz po polsku, jasno i konkretnie.
        Zawsze szukasz rozwiązania problemu klienta.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    history_text = ""
    if customer_history:
        for h in customer_history[-5:]:
            history_text += f"- {h.get('date', '?')}: {h.get('subject', '?')} [{h.get('resolution', '?')}]\n"
    else:
        history_text = "Brak historii"

    task = Task(
        description=f"""
        Przeanalizuj i odpowiedz na zgłoszenie:

        ZGŁOSZENIE:
        Temat: {ticket_subject}
        Treść: {ticket_content}

        KLIENT: {customer_name or "Szanowny Kliencie"}

        HISTORIA KLIENTA:
        {history_text}

        KONTEKST PRODUKTU/USŁUGI:
        {product_context or "Brak dodatkowego kontekstu"}

        FIRMA: {company_name or "[Nazwa firmy]"}

        TON ODPOWIEDZI: {tone}

        ZADANIA:
        1. Przeanalizuj zgłoszenie (kategoria, priorytet, sentyment)
        2. Zidentyfikuj problem klienta
        3. Przygotuj profesjonalną odpowiedź
        4. {"Zaproponuj kolejne kroki" if include_next_steps else ""}

        Zwróć w formacie JSON:
        {{
            "analysis": {{
                "category": "billing/technical/general/complaint/feature_request",
                "priority": "low/medium/high/urgent",
                "sentiment": "positive/neutral/negative/angry",
                "issue_summary": "krótkie podsumowanie problemu",
                "requires_escalation": true/false,
                "escalation_reason": "powód eskalacji (jeśli dotyczy)"
            }},
            "response": {{
                "subject": "Re: temat odpowiedzi",
                "greeting": "powitanie",
                "acknowledgment": "potwierdzenie zrozumienia problemu",
                "solution": "proponowane rozwiązanie",
                "next_steps": ["kolejne kroki"],
                "closing": "zakończenie",
                "full_response": "pełna treść odpowiedzi"
            }},
            "internal_notes": {{
                "root_cause": "przyczyna problemu",
                "suggested_actions": ["sugerowane działania wewnętrzne"],
                "similar_issues": "czy to powtarzający się problem",
                "knowledge_base_update": "czy wymaga aktualizacji bazy wiedzy"
            }},
            "tags": ["tagi do zgłoszenia"]
        }}
        """,
        agent=support_agent,
        expected_output="Ticket handling in JSON format",
    )

    crew = Crew(
        agents=[support_agent],
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
            return {"success": True, "ticket_response": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "ticket_response": {"raw_content": result_text}}


async def suggest_response(
    ticket_content: str,
    response_type: str = "standard",
    tone: str = "professional",
    max_length: int = 500,
) -> dict:
    """Generate a quick response suggestion for a ticket.

    Args:
        ticket_content: Ticket content
        response_type: standard, apology, confirmation, followup
        tone: professional, friendly, formal
        max_length: Maximum response length

    Returns:
        Dictionary with response suggestions
    """
    llm = _get_llm()

    responder = Agent(
        role="Quick Response Specialist",
        goal="Szybko generować skuteczne odpowiedzi na zgłoszenia",
        backstory="""Jesteś ekspertem od szybkich, ale skutecznych odpowiedzi
        w obsłudze klienta. Twoje odpowiedzi są zwięzłe i na temat.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    type_instructions = {
        "standard": "Standardowa odpowiedź na zapytanie",
        "apology": "Przeprosiny za problem/niedogodność",
        "confirmation": "Potwierdzenie otrzymania/wykonania",
        "followup": "Follow-up do poprzedniego zgłoszenia",
    }

    instruction = type_instructions.get(response_type, "Standardowa odpowiedź")

    task = Task(
        description=f"""
        Wygeneruj szybką odpowiedź:

        ZGŁOSZENIE:
        {ticket_content}

        TYP ODPOWIEDZI: {instruction}
        TON: {tone}
        MAX DŁUGOŚĆ: {max_length} znaków

        Zwróć w formacie JSON:
        {{
            "responses": [
                {{
                    "version": "short",
                    "text": "krótka wersja odpowiedzi"
                }},
                {{
                    "version": "standard",
                    "text": "standardowa wersja"
                }},
                {{
                    "version": "detailed",
                    "text": "szczegółowa wersja"
                }}
            ],
            "recommended": "short/standard/detailed"
        }}
        """,
        agent=responder,
        expected_output="Response suggestions in JSON format",
    )

    crew = Crew(
        agents=[responder],
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
            return {"success": True, "suggestions": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "suggestions": {"text": result_text}}


async def categorize_tickets(
    tickets: list[dict],
    custom_categories: list[str] | None = None,
) -> dict:
    """Categorize multiple tickets.

    Args:
        tickets: List of tickets [{"id": "...", "subject": "...", "content": "..."}]
        custom_categories: Custom categories to use

    Returns:
        Dictionary with categorized tickets
    """
    llm = _get_llm()

    categorizer = Agent(
        role="Ticket Categorization Specialist",
        goal="Szybko i dokładnie kategoryzować zgłoszenia",
        backstory="""Jesteś specjalistą od kategoryzacji zgłoszeń.
        Potrafisz szybko ocenić temat i priorytet zgłoszenia.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    default_categories = [
        "billing", "technical", "account", "feature_request",
        "complaint", "general_inquiry", "feedback", "other"
    ]

    categories = custom_categories or default_categories
    categories_text = ", ".join(categories)

    tickets_text = ""
    for t in tickets[:20]:  # Limit to 20 tickets
        tickets_text += f"""
        ID: {t.get('id', 'N/A')}
        Temat: {t.get('subject', 'N/A')}
        Treść: {t.get('content', 'N/A')[:200]}...
        ---"""

    task = Task(
        description=f"""
        Skategoryzuj następujące zgłoszenia:

        DOSTĘPNE KATEGORIE: {categories_text}

        ZGŁOSZENIA:
        {tickets_text}

        Zwróć w formacie JSON:
        {{
            "categorized_tickets": [
                {{
                    "id": "id zgłoszenia",
                    "category": "kategoria",
                    "priority": "low/medium/high/urgent",
                    "confidence": 0.0-1.0
                }}
            ],
            "summary": {{
                "total": liczba,
                "by_category": {{"kategoria": liczba}},
                "by_priority": {{"priorytet": liczba}}
            }}
        }}
        """,
        agent=categorizer,
        expected_output="Categorized tickets in JSON format",
    )

    crew = Crew(
        agents=[categorizer],
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
            return {"success": True, "categorization": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "categorization": {"raw_content": result_text}}

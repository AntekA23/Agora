"""CRM Assistant Agent - Customer data analysis and suggestions."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.6,
        api_key=settings.OPENAI_API_KEY,
    )


async def analyze_customer_data(
    customer_name: str,
    customer_data: dict,
    interaction_history: list[dict] | None = None,
    purchases: list[dict] | None = None,
    support_tickets: list[dict] | None = None,
) -> dict:
    """Analyze customer data and provide insights.

    Args:
        customer_name: Customer/company name
        customer_data: Customer profile data
        interaction_history: List of interactions
        purchases: Purchase history
        support_tickets: Support ticket history

    Returns:
        Dictionary with customer analysis and insights
    """
    llm = _get_llm()

    analyst = Agent(
        role="Customer Success Analyst",
        goal="Analizować dane klientów i dostarczać użyteczne insights",
        backstory="""Jesteś analitykiem Customer Success z doświadczeniem w B2B SaaS.
        Potrafisz wyciągać wnioski z danych CRM i przewidywać zachowania klientów.
        Twoje analizy pomagają zwiększyć retencję i rozwijać klientów.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    # Format data
    profile_text = "\n".join(f"- {k}: {v}" for k, v in customer_data.items())

    history_text = ""
    if interaction_history:
        for h in interaction_history[-10:]:  # Last 10 interactions
            history_text += f"- {h.get('date', '?')}: {h.get('type', '?')} - {h.get('notes', '')}\n"
    else:
        history_text = "Brak danych"

    purchases_text = ""
    if purchases:
        total_value = sum(p.get('value', 0) for p in purchases)
        purchases_text = f"Liczba zakupów: {len(purchases)}, Łączna wartość: {total_value}\n"
        for p in purchases[-5:]:  # Last 5 purchases
            purchases_text += f"- {p.get('date', '?')}: {p.get('product', '?')} - {p.get('value', '?')} PLN\n"
    else:
        purchases_text = "Brak historii zakupów"

    tickets_text = ""
    if support_tickets:
        open_tickets = sum(1 for t in support_tickets if t.get('status') == 'open')
        tickets_text = f"Łącznie ticketów: {len(support_tickets)}, Otwartych: {open_tickets}\n"
        for t in support_tickets[-5:]:
            tickets_text += f"- {t.get('date', '?')}: {t.get('subject', '?')} [{t.get('status', '?')}]\n"
    else:
        tickets_text = "Brak ticketów"

    task = Task(
        description=f"""
        Przeanalizuj dane klienta i dostarcz insights:

        KLIENT: {customer_name}

        PROFIL:
        {profile_text}

        OSTATNIE INTERAKCJE:
        {history_text}

        HISTORIA ZAKUPÓW:
        {purchases_text}

        TICKETY SUPPORTOWE:
        {tickets_text}

        ANALIZA POWINNA ZAWIERAĆ:

        1. HEALTH SCORE (0-100)
           - Engagement score
           - Purchase recency
           - Support satisfaction
           - Risk of churn

        2. CUSTOMER INSIGHTS
           - Kluczowe obserwacje
           - Wzorce zachowań
           - Potencjalne problemy

        3. OPPORTUNITIES
           - Cross-sell/Upsell możliwości
           - Expansion potential
           - Referral potential

        4. RISKS
           - Churn signals
           - Satisfaction issues
           - Missing engagement

        5. RECOMMENDATIONS
           - Konkretne akcje do podjęcia
           - Priorytety

        Zwróć w formacie JSON:
        {{
            "customer": "{customer_name}",
            "health_score": {{
                "overall": 0-100,
                "engagement": 0-100,
                "satisfaction": 0-100,
                "growth_potential": 0-100,
                "churn_risk": "low/medium/high"
            }},
            "insights": [
                {{
                    "type": "positive/negative/neutral",
                    "insight": "obserwacja",
                    "evidence": "na podstawie czego"
                }}
            ],
            "opportunities": [
                {{
                    "type": "upsell/cross-sell/expansion/referral",
                    "description": "opis szansy",
                    "potential_value": "szacowana wartość",
                    "probability": "high/medium/low"
                }}
            ],
            "risks": [
                {{
                    "risk": "opis ryzyka",
                    "severity": "high/medium/low",
                    "mitigation": "jak zaradzić"
                }}
            ],
            "recommended_actions": [
                {{
                    "action": "co zrobić",
                    "priority": "high/medium/low",
                    "owner": "kto powinien",
                    "deadline": "kiedy"
                }}
            ],
            "summary": "podsumowanie 2-3 zdania"
        }}
        """,
        agent=analyst,
        expected_output="Customer analysis in JSON format",
    )

    crew = Crew(
        agents=[analyst],
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

    return {"success": True, "analysis": {"raw_content": result_text}}


async def suggest_next_actions(
    customer_name: str,
    last_interaction: dict | None = None,
    customer_stage: str = "active",
    days_since_contact: int = 0,
    open_opportunities: list[dict] | None = None,
) -> dict:
    """Suggest next best actions for a customer.

    Args:
        customer_name: Customer name
        last_interaction: Details of last interaction
        customer_stage: prospect, new, active, at_risk, churned
        days_since_contact: Days since last contact
        open_opportunities: Current open opportunities

    Returns:
        Dictionary with suggested actions
    """
    llm = _get_llm()

    advisor = Agent(
        role="Sales Action Advisor",
        goal="Rekomendować optymalne następne kroki w relacji z klientem",
        backstory="""Jesteś doświadczonym doradcą sprzedaży B2B.
        Wiesz, kiedy i jak kontaktować się z klientami,
        aby maksymalizować szanse na sukces.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    last_interaction_text = ""
    if last_interaction:
        last_interaction_text = f"""
        Ostatnia interakcja:
        - Data: {last_interaction.get('date', '?')}
        - Typ: {last_interaction.get('type', '?')}
        - Notatki: {last_interaction.get('notes', '?')}
        """

    opportunities_text = ""
    if open_opportunities:
        for opp in open_opportunities:
            opportunities_text += f"- {opp.get('name', '?')}: {opp.get('value', '?')} PLN, stage: {opp.get('stage', '?')}\n"

    task = Task(
        description=f"""
        Zasugeruj następne najlepsze akcje dla klienta:

        KLIENT: {customer_name}
        STATUS: {customer_stage}
        DNI OD KONTAKTU: {days_since_contact}

        {last_interaction_text}

        OTWARTE SZANSE:
        {opportunities_text or "Brak"}

        Zwróć w formacie JSON:
        {{
            "customer": "{customer_name}",
            "urgency": "high/medium/low",
            "suggested_actions": [
                {{
                    "action": "opis akcji",
                    "type": "call/email/meeting/demo/proposal",
                    "priority": 1-5,
                    "reasoning": "dlaczego ta akcja",
                    "best_timing": "kiedy najlepiej",
                    "talking_points": ["punkty do poruszenia"],
                    "expected_outcome": "oczekiwany rezultat"
                }}
            ],
            "avoid": ["czego unikać"],
            "context_to_remember": ["ważny kontekst"]
        }}
        """,
        agent=advisor,
        expected_output="Action suggestions in JSON format",
    )

    crew = Crew(
        agents=[advisor],
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

    return {"success": True, "suggestions": {"raw_content": result_text}}


async def generate_followup_email(
    customer_name: str,
    contact_name: str,
    context: str,
    email_purpose: str = "followup",
    previous_conversation: str = "",
    tone: str = "professional",
    include_cta: bool = True,
) -> dict:
    """Generate a follow-up email for a customer.

    Args:
        customer_name: Company name
        contact_name: Contact person name
        context: Context for the email
        email_purpose: followup, thankyou, proposal, reminder, checkin
        previous_conversation: Summary of previous conversation
        tone: professional, friendly, formal
        include_cta: Include call to action

    Returns:
        Dictionary with email content
    """
    llm = _get_llm()

    copywriter = Agent(
        role="Sales Email Copywriter",
        goal="Pisać skuteczne emaile sprzedażowe, które generują odpowiedzi",
        backstory="""Jesteś copywriterem specjalizującym się w emailach B2B.
        Twoje emaile mają wysoki open rate i response rate.
        Piszesz po polsku, profesjonalnie ale ludzko.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    purpose_map = {
        "followup": "follow-up po rozmowie",
        "thankyou": "podziękowanie",
        "proposal": "przesłanie oferty",
        "reminder": "przypomnienie",
        "checkin": "sprawdzenie jak idzie",
    }

    purpose_text = purpose_map.get(email_purpose, email_purpose)

    task = Task(
        description=f"""
        Napisz email do klienta:

        ODBIORCA:
        - Firma: {customer_name}
        - Osoba: {contact_name}

        CEL: {purpose_text}
        TON: {tone}

        KONTEKST:
        {context}

        POPRZEDNIA ROZMOWA:
        {previous_conversation or "Brak szczegółów"}

        WYTYCZNE:
        1. Krótki, konkretny (max 150 słów)
        2. Spersonalizowany - nawiąż do kontekstu
        3. {'Zawrzyj jasne CTA' if include_cta else 'Bez nachalnego CTA'}
        4. Profesjonalny ale ludzki ton
        5. Jeden główny przekaz

        Zwróć w formacie JSON:
        {{
            "subject_options": ["3 propozycje tematu"],
            "email_body": "treść emaila",
            "cta": "call to action (jeśli dotyczy)",
            "best_send_time": "najlepszy czas wysyłki",
            "follow_up_if_no_response": "co zrobić jeśli brak odpowiedzi"
        }}
        """,
        agent=copywriter,
        expected_output="Email content in JSON format",
    )

    crew = Crew(
        agents=[copywriter],
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
            return {"success": True, "email": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "email": {"body": result_text}}

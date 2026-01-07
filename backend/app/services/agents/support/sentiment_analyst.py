"""Sentiment Analyst Agent - Analyzing customer sentiment."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,  # Lower for more consistent analysis
        api_key=settings.OPENAI_API_KEY,
    )


async def analyze_sentiment(
    text: str,
    context: str = "",
    include_emotions: bool = True,
    include_intent: bool = True,
) -> dict:
    """Analyze sentiment of a single text.

    Args:
        text: Text to analyze
        context: Additional context (e.g., product, previous interaction)
        include_emotions: Detect specific emotions
        include_intent: Detect customer intent

    Returns:
        Dictionary with sentiment analysis
    """
    llm = _get_llm()

    analyst = Agent(
        role="Sentiment Analysis Specialist",
        goal="Dokładnie analizować sentyment i emocje w tekście",
        backstory="""Jesteś ekspertem od analizy sentymentu w języku polskim.
        Rozpoznajesz niuanse emocjonalne, sarkazm i ukryte intencje.
        Twoje analizy pomagają firmom lepiej rozumieć klientów.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    extras = ""
    if include_emotions:
        extras += """
        WYKRYJ EMOCJE:
        - złość, frustracja, rozczarowanie
        - zadowolenie, radość, wdzięczność
        - zmieszanie, niepewność
        - obojętność, neutralność
        """
    if include_intent:
        extras += """
        WYKRYJ INTENCJĘ:
        - chęć zakupu
        - ryzyko odejścia (churn)
        - potrzeba wsparcia
        - feedback/sugestia
        - reklamacja
        """

    task = Task(
        description=f"""
        Przeanalizuj sentyment tekstu:

        TEKST:
        "{text}"

        KONTEKST: {context or "brak"}

        {extras}

        Zwróć w formacie JSON:
        {{
            "sentiment": {{
                "label": "positive/negative/neutral/mixed",
                "score": -1.0 to 1.0,
                "confidence": 0.0 to 1.0
            }},
            "emotions": [
                {{
                    "emotion": "nazwa emocji",
                    "intensity": "low/medium/high",
                    "evidence": "fragment tekstu"
                }}
            ],
            "intent": {{
                "primary": "główna intencja",
                "secondary": ["dodatkowe intencje"],
                "churn_risk": "low/medium/high",
                "purchase_intent": "low/medium/high"
            }},
            "key_phrases": {{
                "positive": ["pozytywne frazy"],
                "negative": ["negatywne frazy"],
                "neutral": ["neutralne frazy"]
            }},
            "language_features": {{
                "tone": "formalny/nieformalny/agresywny/przyjazny",
                "urgency": "low/medium/high",
                "sarcasm_detected": true/false
            }},
            "recommended_response_tone": "ton zalecany w odpowiedzi",
            "summary": "1-2 zdania podsumowania"
        }}
        """,
        agent=analyst,
        expected_output="Sentiment analysis in JSON format",
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


async def analyze_feedback_batch(
    feedback_items: list[dict],
    group_by: str = "sentiment",
) -> dict:
    """Analyze sentiment of multiple feedback items.

    Args:
        feedback_items: List of feedback [{"id": "...", "text": "...", "source": "..."}]
        group_by: How to group results (sentiment, source, topic)

    Returns:
        Dictionary with batch analysis
    """
    llm = _get_llm()

    batch_analyst = Agent(
        role="Feedback Analysis Specialist",
        goal="Analizować zbiorczo opinie i identyfikować trendy",
        backstory="""Jesteś analitykiem opinii klientów.
        Potrafisz szybko przeanalizować wiele opinii i wyciągnąć wnioski.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    feedback_text = ""
    for f in feedback_items[:50]:  # Limit to 50 items
        feedback_text += f"""
        ID: {f.get('id', 'N/A')}
        Źródło: {f.get('source', 'N/A')}
        Tekst: {f.get('text', 'N/A')[:200]}
        ---"""

    task = Task(
        description=f"""
        Przeanalizuj zbiorczo opinie:

        {feedback_text}

        GRUPUJ WG: {group_by}

        Zwróć w formacie JSON:
        {{
            "summary": {{
                "total_analyzed": liczba,
                "positive_percent": procent,
                "negative_percent": procent,
                "neutral_percent": procent,
                "average_sentiment_score": -1.0 to 1.0
            }},
            "by_sentiment": {{
                "positive": [
                    {{"id": "id", "score": 0.0-1.0, "key_phrase": "główna fraza"}}
                ],
                "negative": [...],
                "neutral": [...]
            }},
            "trending_topics": [
                {{
                    "topic": "temat",
                    "count": liczba,
                    "sentiment": "positive/negative/mixed"
                }}
            ],
            "key_insights": [
                {{
                    "insight": "wniosek",
                    "evidence_count": liczba,
                    "importance": "high/medium/low"
                }}
            ],
            "recommended_actions": [
                {{
                    "action": "rekomendacja",
                    "priority": "high/medium/low",
                    "based_on": "na podstawie czego"
                }}
            ],
            "alerts": [
                {{
                    "type": "churn_risk/urgent_issue/trending_complaint",
                    "description": "opis",
                    "affected_items": ["id"]
                }}
            ]
        }}
        """,
        agent=batch_analyst,
        expected_output="Batch analysis in JSON format",
    )

    crew = Crew(
        agents=[batch_analyst],
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
            return {"success": True, "batch_analysis": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "batch_analysis": {"raw_content": result_text}}


async def generate_sentiment_report(
    period: str,
    feedback_summary: dict,
    comparison_period: dict | None = None,
) -> dict:
    """Generate a sentiment report for a period.

    Args:
        period: Report period (e.g., "Styczeń 2025")
        feedback_summary: Summary data for the period
        comparison_period: Previous period data for comparison

    Returns:
        Dictionary with sentiment report
    """
    llm = _get_llm()

    reporter = Agent(
        role="Customer Insights Reporter",
        goal="Tworzyć przejrzyste raporty z analizy sentymentu",
        backstory="""Jesteś analitykiem tworzącym raporty dla zarządu.
        Piszesz zwięźle, z naciskiem na actionable insights.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    summary_text = f"""
    PODSUMOWANIE OKRESU:
    - Łączna liczba opinii: {feedback_summary.get('total', 'N/A')}
    - Pozytywne: {feedback_summary.get('positive_percent', 'N/A')}%
    - Negatywne: {feedback_summary.get('negative_percent', 'N/A')}%
    - Średni wynik: {feedback_summary.get('avg_score', 'N/A')}
    - Główne tematy: {', '.join(feedback_summary.get('top_topics', []))}
    """

    comparison_text = ""
    if comparison_period:
        comparison_text = f"""
        PORÓWNANIE Z POPRZEDNIM OKRESEM:
        - Zmiana pozytywnych: {comparison_period.get('positive_change', 'N/A')}%
        - Zmiana negatywnych: {comparison_period.get('negative_change', 'N/A')}%
        - Zmiana średniego wyniku: {comparison_period.get('score_change', 'N/A')}
        """

    task = Task(
        description=f"""
        Stwórz raport sentymentu za okres: {period}

        {summary_text}

        {comparison_text}

        RAPORT POWINIEN ZAWIERAĆ:
        1. Executive Summary (3-4 zdania)
        2. Kluczowe metryki
        3. Trendy i zmiany
        4. Główne problemy
        5. Pozytywne aspekty
        6. Rekomendacje

        Zwróć w formacie JSON:
        {{
            "report_title": "Raport Sentymentu - {period}",
            "executive_summary": "podsumowanie 3-4 zdania",
            "metrics": {{
                "nps_equivalent": liczba,
                "satisfaction_index": 0-100,
                "response_needed_percent": procent
            }},
            "highlights": [
                {{
                    "type": "positive/negative/trend",
                    "title": "tytuł",
                    "description": "opis",
                    "data": "dane"
                }}
            ],
            "top_issues": [
                {{
                    "issue": "problem",
                    "frequency": liczba,
                    "severity": "high/medium/low",
                    "trend": "increasing/stable/decreasing"
                }}
            ],
            "recommendations": [
                {{
                    "recommendation": "rekomendacja",
                    "expected_impact": "oczekiwany wpływ",
                    "priority": "high/medium/low"
                }}
            ],
            "full_report_text": "pełny tekst raportu w Markdown"
        }}
        """,
        agent=reporter,
        expected_output="Sentiment report in JSON format",
    )

    crew = Crew(
        agents=[reporter],
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
            return {"success": True, "report": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "report": {"full_report_text": result_text}}

"""FAQ Generator Agent - Creating FAQ from tickets."""

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


async def generate_faq_from_tickets(
    tickets: list[dict],
    product_name: str = "",
    existing_faq: list[dict] | None = None,
    max_questions: int = 10,
    target_audience: str = "general",
) -> dict:
    """Generate FAQ entries from support tickets.

    Args:
        tickets: List of tickets [{"subject": "...", "content": "...", "resolution": "..."}]
        product_name: Name of product/service
        existing_faq: Existing FAQ to avoid duplicates
        max_questions: Maximum number of questions to generate
        target_audience: general, technical, business

    Returns:
        Dictionary with generated FAQ
    """
    llm = _get_llm()

    faq_creator = Agent(
        role="FAQ Content Creator",
        goal="Tworzyć pomocne FAQ na podstawie rzeczywistych zgłoszeń klientów",
        backstory="""Jesteś specjalistą od tworzenia treści pomocy.
        Potrafisz wyciągnąć najważniejsze pytania z zgłoszeń klientów
        i tworzyć jasne, pomocne odpowiedzi. Piszesz po polsku.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    tickets_text = ""
    for t in tickets[:30]:
        tickets_text += f"""
        Temat: {t.get('subject', 'N/A')}
        Problem: {t.get('content', 'N/A')[:300]}
        Rozwiązanie: {t.get('resolution', 'N/A')[:300]}
        ---"""

    existing_text = ""
    if existing_faq:
        existing_text = "ISTNIEJĄCE FAQ (nie duplikuj):\n"
        for faq in existing_faq:
            existing_text += f"- {faq.get('question', '')}\n"

    task = Task(
        description=f"""
        Stwórz FAQ na podstawie zgłoszeń:

        PRODUKT/USŁUGA: {product_name or "[Produkt]"}
        ODBIORCY: {target_audience}
        MAX PYTAŃ: {max_questions}

        {existing_text}

        ZGŁOSZENIA DO ANALIZY:
        {tickets_text}

        WYTYCZNE:
        1. Zidentyfikuj najczęściej powtarzające się pytania
        2. Sformułuj pytania tak, jak zadałby je klient
        3. Odpowiedzi powinny być konkretne i pomocne
        4. Unikaj żargonu technicznego (chyba że target to technical)
        5. Grupuj powiązane pytania w kategorie

        Zwróć w formacie JSON:
        {{
            "faq_entries": [
                {{
                    "id": "faq_1",
                    "category": "kategoria",
                    "question": "pytanie",
                    "answer": "odpowiedź",
                    "short_answer": "krótka odpowiedź (1 zdanie)",
                    "keywords": ["słowa kluczowe"],
                    "related_questions": ["powiązane pytania"],
                    "source_tickets_count": liczba_zgłoszeń
                }}
            ],
            "categories": [
                {{
                    "name": "nazwa kategorii",
                    "description": "opis",
                    "question_count": liczba
                }}
            ],
            "insights": {{
                "most_common_issues": ["najczęstsze problemy"],
                "suggested_improvements": ["sugestie ulepszeń produktu"],
                "gaps_in_documentation": ["braki w dokumentacji"]
            }}
        }}
        """,
        agent=faq_creator,
        expected_output="FAQ in JSON format",
    )

    crew = Crew(
        agents=[faq_creator],
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
            return {"success": True, "faq": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "faq": {"raw_content": result_text}}


async def generate_help_article(
    topic: str,
    target_audience: str = "general",
    article_type: str = "how_to",
    product_context: str = "",
    include_screenshots_placeholders: bool = True,
    include_video_suggestions: bool = False,
) -> dict:
    """Generate a help article/documentation.

    Args:
        topic: Article topic
        target_audience: general, technical, beginner, advanced
        article_type: how_to, troubleshooting, overview, reference
        product_context: Context about the product
        include_screenshots_placeholders: Include placeholders for screenshots
        include_video_suggestions: Include video content suggestions

    Returns:
        Dictionary with article content
    """
    llm = _get_llm()

    content_writer = Agent(
        role="Technical Writer",
        goal="Tworzyć jasne i pomocne artykuły pomocy",
        backstory="""Jesteś technicznym pisarzem z doświadczeniem w tworzeniu
        dokumentacji użytkownika. Piszesz jasno, krok po kroku,
        tak aby nawet początkujący mógł wykonać instrukcje.
        Piszesz po polsku.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    type_instructions = {
        "how_to": "Instrukcja krok po kroku jak coś zrobić",
        "troubleshooting": "Rozwiązywanie problemów - diagnoza i naprawa",
        "overview": "Przegląd funkcjonalności lub koncepcji",
        "reference": "Dokumentacja referencyjna z detalami technicznymi",
    }

    article_instruction = type_instructions.get(article_type, "Artykuł informacyjny")

    task = Task(
        description=f"""
        Stwórz artykuł pomocy:

        TEMAT: {topic}
        TYP: {article_instruction}
        ODBIORCY: {target_audience}

        KONTEKST PRODUKTU:
        {product_context or "Ogólna platforma/aplikacja"}

        WYTYCZNE:
        1. Jasny, opisowy tytuł
        2. Krótkie wprowadzenie (co użytkownik osiągnie)
        3. {"Numerowane kroki z jasnym opisem" if article_type == "how_to" else "Logiczna struktura sekcji"}
        4. {"Miejsca na screenshoty [SCREENSHOT: opis]" if include_screenshots_placeholders else ""}
        5. {"Sugestie treści video" if include_video_suggestions else ""}
        6. Sekcja FAQ lub częste problemy
        7. Powiązane artykuły

        Zwróć w formacie JSON:
        {{
            "title": "tytuł artykułu",
            "meta_description": "opis do wyszukiwarek (max 160 znaków)",
            "introduction": "wprowadzenie",
            "prerequisites": ["wymagania wstępne"],
            "sections": [
                {{
                    "title": "tytuł sekcji",
                    "content": "treść sekcji",
                    "steps": ["kroki (jeśli dotyczy)"],
                    "screenshot_placeholders": ["opisy screenshotów"],
                    "tips": ["wskazówki"],
                    "warnings": ["ostrzeżenia"]
                }}
            ],
            "faq": [
                {{"question": "pytanie", "answer": "odpowiedź"}}
            ],
            "related_articles": ["powiązane tematy"],
            "video_suggestions": ["sugestie video (jeśli dotyczy)"],
            "full_text": "pełna treść artykułu w Markdown",
            "estimated_read_time": "X min"
        }}
        """,
        agent=content_writer,
        expected_output="Help article in JSON format",
    )

    crew = Crew(
        agents=[content_writer],
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
            return {"success": True, "article": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "article": {"full_text": result_text}}

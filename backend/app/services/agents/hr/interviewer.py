"""HR Interviewer Agent - Interview question preparation."""

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


async def generate_interview_questions(
    position: str,
    department: str,
    experience_level: str = "mid",
    skills: list[str] | None = None,
    interview_type: str = "technical",
    company_values: list[str] | None = None,
    duration_minutes: int = 60,
    use_web_search: bool = True,
) -> dict:
    """Generate interview questions for a position.

    Args:
        position: Job title
        department: Department name
        experience_level: junior, mid, senior, lead
        skills: Key skills to assess
        interview_type: technical, behavioral, cultural, mixed
        company_values: Company values to assess cultural fit
        duration_minutes: Interview duration
        use_web_search: Research latest interview trends

    Returns:
        Dictionary with interview questions and structure
    """
    llm = _get_llm()

    tools = [search_tool] if use_web_search and settings.TAVILY_API_KEY else []

    interviewer = Agent(
        role="Senior HR Interviewer",
        goal="Przygotować kompleksowy zestaw pytań rekrutacyjnych oceniających kandydata",
        backstory="""Jesteś doświadczonym rekruterem z 15-letnim stażem.
        Przeprowadziłeś tysiące rozmów kwalifikacyjnych w Polsce.
        Wiesz jak zadawać pytania, które naprawdę pozwalają ocenić kandydata.
        Znasz techniki STAR, pytania behawioralne i techniczne.
        Zawsze przygotowujesz pytania po polsku.""",
        tools=tools,
        llm=llm,
        verbose=False,
    )

    skills_text = ", ".join(skills or ["ogólne kompetencje"])
    values_text = ", ".join(company_values or ["profesjonalizm", "współpraca"])

    num_questions = duration_minutes // 5  # ~5 min per question

    research_context = ""
    if use_web_search and tools:
        research_context = f"""
        NAJPIERW przeprowadź research:
        1. Sprawdź najnowsze trendy w rekrutacji na stanowisko {position}
        2. Zobacz jakie pytania są teraz popularne w branży
        3. Znajdź przykłady dobrych pytań technicznych dla {skills_text}
        """

    task = Task(
        description=f"""
        {research_context}

        Przygotuj zestaw pytań na rozmowę rekrutacyjną:

        DANE:
        - Stanowisko: {position}
        - Dział: {department}
        - Poziom: {experience_level}
        - Typ rozmowy: {interview_type}
        - Czas trwania: {duration_minutes} minut
        - Liczba pytań: około {num_questions}

        UMIEJĘTNOŚCI DO OCENY:
        {skills_text}

        WARTOŚCI FIRMOWE:
        {values_text}

        STRUKTURA ROZMOWY:

        1. WPROWADZENIE (5 min)
           - Ice-breaker
           - Przedstawienie firmy i stanowiska

        2. PYTANIA O DOŚWIADCZENIE (15-20 min)
           - Dotychczasowa kariera
           - Kluczowe projekty
           - Metoda STAR

        3. PYTANIA TECHNICZNE/MERYTORYCZNE (20-25 min)
           - Wiedza specjalistyczna
           - Case studies
           - Rozwiązywanie problemów

        4. PYTANIA BEHAWIORALNE (10-15 min)
           - Praca w zespole
           - Radzenie sobie ze stresem
           - Konflikty i wyzwania

        5. PYTANIA O KULTURĘ (5-10 min)
           - Dopasowanie do wartości
           - Motywacja
           - Oczekiwania

        6. PYTANIA KANDYDATA (5 min)
           - Przestrzeń na pytania

        Zwróć w formacie JSON:
        {{
            "position": "{position}",
            "duration_minutes": {duration_minutes},
            "structure": [
                {{
                    "phase": "nazwa fazy",
                    "duration_minutes": x,
                    "questions": [
                        {{
                            "question": "treść pytania",
                            "purpose": "co oceniamy",
                            "follow_ups": ["pytania pogłębiające"],
                            "red_flags": ["na co uważać"],
                            "green_flags": ["czego szukamy"]
                        }}
                    ]
                }}
            ],
            "scoring_criteria": [
                {{
                    "criterion": "nazwa kryterium",
                    "weight": 1-5,
                    "description": "jak oceniać"
                }}
            ],
            "tips": ["wskazówki dla prowadzącego rozmowę"]
        }}
        """,
        agent=interviewer,
        expected_output="Interview questions in JSON format",
    )

    crew = Crew(
        agents=[interviewer],
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
                "interview": parsed,
                "position": position,
                "interview_type": interview_type,
            }
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "interview": {"raw_content": result_text},
        "position": position,
        "interview_type": interview_type,
    }


async def generate_candidate_scorecard(
    position: str,
    skills: list[str],
    experience_level: str = "mid",
) -> dict:
    """Generate a scorecard template for evaluating candidates.

    Args:
        position: Job title
        skills: Skills to evaluate
        experience_level: Expected experience level

    Returns:
        Dictionary with scorecard template
    """
    llm = _get_llm()

    hr_expert = Agent(
        role="HR Assessment Expert",
        goal="Stworzyć obiektywny system oceny kandydatów",
        backstory="""Jesteś ekspertem od oceny kandydatów z wieloletnim doświadczeniem.
        Tworzysz sprawiedliwe i mierzalne systemy oceny.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    skills_text = ", ".join(skills)

    task = Task(
        description=f"""
        Stwórz kartę oceny kandydata dla stanowiska: {position}
        Poziom: {experience_level}
        Umiejętności do oceny: {skills_text}

        Zwróć w formacie JSON:
        {{
            "position": "{position}",
            "categories": [
                {{
                    "name": "nazwa kategorii",
                    "weight_percent": 20,
                    "criteria": [
                        {{
                            "name": "kryterium",
                            "description": "co oceniamy",
                            "scale": "1-5",
                            "anchors": {{
                                "1": "opis dla 1",
                                "3": "opis dla 3",
                                "5": "opis dla 5"
                            }}
                        }}
                    ]
                }}
            ],
            "overall_recommendation": {{
                "strong_hire": ">=4.5",
                "hire": ">=3.5",
                "maybe": ">=2.5",
                "no_hire": "<2.5"
            }},
            "notes_sections": ["sekcje na notatki"]
        }}
        """,
        agent=hr_expert,
        expected_output="Candidate scorecard in JSON format",
    )

    crew = Crew(
        agents=[hr_expert],
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
            return {"success": True, "scorecard": parsed}
        except json.JSONDecodeError:
            pass

    return {"success": True, "scorecard": {"raw_content": result_text}}

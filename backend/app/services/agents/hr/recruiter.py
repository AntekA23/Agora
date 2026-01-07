"""HR Recruiter Agent - Job postings and salary research."""

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


async def generate_job_posting(
    position: str,
    department: str,
    requirements: list[str],
    responsibilities: list[str],
    company_name: str = "",
    company_description: str = "",
    location: str = "Polska",
    employment_type: str = "pełny etat",
    experience_level: str = "mid",
    salary_range: str = "",
    benefits: list[str] | None = None,
    use_web_search: bool = True,
) -> dict:
    """Generate a professional job posting.

    Args:
        position: Job title (e.g., "Senior Python Developer")
        department: Department name (e.g., "IT", "Marketing")
        requirements: List of required skills/qualifications
        responsibilities: List of job responsibilities
        company_name: Company name for context
        company_description: Brief company description
        location: Job location
        employment_type: Full-time, part-time, contract, etc.
        experience_level: junior, mid, senior, lead
        salary_range: Optional salary range to include
        benefits: List of benefits offered
        use_web_search: Whether to research market trends

    Returns:
        Dictionary with job posting content
    """
    llm = _get_llm()

    tools = [search_tool] if use_web_search and settings.TAVILY_API_KEY else []

    recruiter = Agent(
        role="HR Recruiter Specialist",
        goal="Tworzyć atrakcyjne ogłoszenia o pracę, które przyciągają najlepszych kandydatów",
        backstory="""Jesteś doświadczonym rekruterem z 10-letnim stażem w Polsce.
        Znasz polski rynek pracy, trendy rekrutacyjne i wiesz jak pisać ogłoszenia,
        które wyróżniają się na tle konkurencji. Piszesz po polsku, profesjonalnie
        ale przyjaźnie. Znasz specyfikę różnych branż i stanowisk.""",
        tools=tools,
        llm=llm,
        verbose=False,
    )

    benefits_text = "\n".join(f"- {b}" for b in (benefits or []))
    requirements_text = "\n".join(f"- {r}" for r in requirements)
    responsibilities_text = "\n".join(f"- {r}" for r in responsibilities)

    research_context = ""
    if use_web_search and tools:
        research_context = f"""
        NAJPIERW przeprowadź research:
        1. Sprawdź aktualne trendy rekrutacyjne dla stanowiska {position}
        2. Zobacz jakie benefity oferuje konkurencja
        3. Sprawdź jakie umiejętności są teraz najbardziej poszukiwane
        """

    task = Task(
        description=f"""
        {research_context}

        Stwórz profesjonalne ogłoszenie o pracę w języku polskim:

        DANE STANOWISKA:
        - Stanowisko: {position}
        - Dział: {department}
        - Lokalizacja: {location}
        - Typ zatrudnienia: {employment_type}
        - Poziom doświadczenia: {experience_level}
        - Widełki płacowe: {salary_range or "do negocjacji"}

        FIRMA:
        {company_name}
        {company_description}

        WYMAGANIA:
        {requirements_text}

        OBOWIĄZKI:
        {responsibilities_text}

        BENEFITY:
        {benefits_text or "Standardowy pakiet benefitów"}

        WYTYCZNE:
        1. Zacznij od chwytliwego wprowadzenia o firmie i stanowisku
        2. Opisz wyzwania i możliwości rozwoju
        3. Wymagania podziel na "must have" i "nice to have"
        4. Podkreśl kulturę organizacyjną i atmosferę
        5. Zakończ jasnym CTA (jak aplikować)
        6. Użyj języka inkluzywnego
        7. Unikaj korporacyjnego żargonu

        Zwróć ogłoszenie w formacie JSON:
        {{
            "title": "tytuł ogłoszenia",
            "intro": "wprowadzenie 2-3 zdania",
            "about_company": "o firmie",
            "about_role": "o stanowisku i wyzwaniach",
            "responsibilities": ["lista obowiązków"],
            "requirements_must": ["wymagania obowiązkowe"],
            "requirements_nice": ["mile widziane"],
            "benefits": ["lista benefitów"],
            "salary_info": "informacja o wynagrodzeniu",
            "how_to_apply": "jak aplikować",
            "full_text": "pełna treść ogłoszenia jako tekst"
        }}
        """,
        agent=recruiter,
        expected_output="Job posting in JSON format",
    )

    crew = Crew(
        agents=[recruiter],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    # Parse result
    import json
    import re

    result_text = str(result)

    # Try to extract JSON
    json_match = re.search(r'\{[\s\S]*\}', result_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return {
                "success": True,
                "job_posting": parsed,
                "position": position,
                "department": department,
            }
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "job_posting": {
            "full_text": result_text,
            "title": position,
        },
        "position": position,
        "department": department,
    }


async def research_salary_market(
    position: str,
    location: str = "Polska",
    experience_level: str = "mid",
) -> dict:
    """Research salary market for a position.

    Args:
        position: Job title to research
        location: Location for salary data
        experience_level: junior, mid, senior

    Returns:
        Dictionary with salary research results
    """
    if not settings.TAVILY_API_KEY:
        return {
            "success": False,
            "error": "Tavily API key not configured for market research",
        }

    llm = _get_llm()

    researcher = Agent(
        role="HR Market Researcher",
        goal="Dostarczyć aktualne dane o wynagrodzeniach i trendach rynkowych",
        backstory="""Jesteś analitykiem rynku pracy specjalizującym się w Polsce.
        Masz dostęp do aktualnych danych o wynagrodzeniach i znasz trendy.""",
        tools=[search_tool],
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""
        Przeprowadź research wynagrodzeń dla:
        - Stanowisko: {position}
        - Lokalizacja: {location}
        - Poziom doświadczenia: {experience_level}

        Wyszukaj:
        1. Aktualne widełki płacowe dla tego stanowiska w Polsce
        2. Porównanie Warszawa vs inne miasta
        3. Trendy - czy wynagrodzenia rosną/maleją
        4. Jakie benefity są standardem

        Zwróć w formacie JSON:
        {{
            "position": "{position}",
            "experience_level": "{experience_level}",
            "salary_range": {{
                "min": liczba,
                "max": liczba,
                "median": liczba,
                "currency": "PLN"
            }},
            "salary_by_city": {{
                "Warszawa": {{"min": x, "max": y}},
                "Kraków": {{"min": x, "max": y}},
                "inne": {{"min": x, "max": y}}
            }},
            "market_trend": "rosnący/stabilny/malejący",
            "common_benefits": ["lista"],
            "insights": "dodatkowe spostrzeżenia",
            "sources": ["źródła danych"]
        }}
        """,
        agent=researcher,
        expected_output="Salary research in JSON format",
    )

    crew = Crew(
        agents=[researcher],
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
            return {"success": True, "research": parsed}
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "research": {"raw_data": result_text},
    }

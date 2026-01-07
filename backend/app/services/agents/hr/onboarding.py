"""HR Onboarding Agent - Onboarding materials and checklists."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY,
    )


async def generate_onboarding_plan(
    position: str,
    department: str,
    employee_name: str = "",
    start_date: str = "",
    manager_name: str = "",
    buddy_name: str = "",
    company_name: str = "",
    onboarding_duration_days: int = 30,
    remote: bool = False,
    tools_and_systems: list[str] | None = None,
    team_members: list[str] | None = None,
) -> dict:
    """Generate a comprehensive onboarding plan.

    Args:
        position: New employee's position
        department: Department name
        employee_name: Name of new employee
        start_date: Start date
        manager_name: Direct manager name
        buddy_name: Assigned buddy name
        company_name: Company name
        onboarding_duration_days: Onboarding period length
        remote: Whether employee is remote
        tools_and_systems: Systems to learn
        team_members: Team member names for introductions

    Returns:
        Dictionary with complete onboarding plan
    """
    llm = _get_llm()

    onboarding_specialist = Agent(
        role="Onboarding Specialist",
        goal="Stworzyć kompleksowy plan wdrożenia nowego pracownika",
        backstory="""Jesteś specjalistą od onboardingu z wieloletnim doświadczeniem.
        Wiesz, że pierwsze 30 dni decyduje o sukcesie pracownika w firmie.
        Tworzysz szczegółowe plany, które pomagają nowym osobom szybko
        się zaaklimatyzować i stać się produktywnymi. Piszesz po polsku.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    tools_text = ", ".join(tools_and_systems or ["standardowe narzędzia biurowe"])
    team_text = ", ".join(team_members or ["zespół"])
    work_mode = "zdalnej" if remote else "stacjonarnej"

    task = Task(
        description=f"""
        Stwórz kompleksowy plan onboardingu:

        DANE PRACOWNIKA:
        - Imię: {employee_name or "[Nowy pracownik]"}
        - Stanowisko: {position}
        - Dział: {department}
        - Data rozpoczęcia: {start_date or "[Data startu]"}
        - Przełożony: {manager_name or "[Manager]"}
        - Buddy: {buddy_name or "[Buddy]"}
        - Tryb pracy: {work_mode}

        FIRMA: {company_name or "[Nazwa firmy]"}

        SYSTEMY DO NAUKI:
        {tools_text}

        CZŁONKOWIE ZESPOŁU:
        {team_text}

        OKRES WDROŻENIA: {onboarding_duration_days} dni

        STWÓRZ PLAN ZAWIERAJĄCY:

        1. PRZED PIERWSZYM DNIEM (preboarding)
           - Co przygotować
           - Jakie dostępy zamówić
           - Komunikacja z nowym pracownikiem

        2. DZIEŃ 1 - Powitanie
           - Harmonogram pierwszego dnia
           - Kto spotyka pracownika
           - Formalności do załatwienia
           - Pierwsze wrażenie

        3. TYDZIEŃ 1 - Orientacja
           - Poznanie zespołu i firmy
           - Szkolenia wstępne
           - Konfiguracja narzędzi
           - Cele na pierwszy tydzień

        4. TYDZIEŃ 2-4 - Nauka
           - Szczegółowe szkolenia
           - Pierwsze zadania
           - Spotkania 1:1
           - Checkpointy

        5. MIESIĄC 2+ - Samodzielność
           - Zwiększanie odpowiedzialności
           - Ocena postępów
           - Feedback

        Zwróć w formacie JSON:
        {{
            "employee": {{
                "name": "{employee_name or 'Nowy pracownik'}",
                "position": "{position}",
                "department": "{department}",
                "start_date": "{start_date}",
                "manager": "{manager_name}",
                "buddy": "{buddy_name}"
            }},
            "preboarding": {{
                "tasks": [
                    {{"task": "opis", "responsible": "kto", "deadline": "kiedy"}}
                ],
                "welcome_message_template": "szablon wiadomości powitalnej"
            }},
            "day_1": {{
                "schedule": [
                    {{"time": "9:00", "activity": "opis", "with": "z kim"}}
                ],
                "checklist": ["lista rzeczy do zrobienia"]
            }},
            "week_1": {{
                "goals": ["cele"],
                "meetings": [
                    {{"day": 1, "title": "tytuł", "participants": ["kto"]}}
                ],
                "trainings": ["szkolenia"],
                "tasks": ["zadania"]
            }},
            "weeks_2_4": {{
                "weekly_goals": {{
                    "week_2": ["cele"],
                    "week_3": ["cele"],
                    "week_4": ["cele"]
                }},
                "checkpoints": [
                    {{"day": 14, "type": "1:1", "topics": ["tematy"]}}
                ],
                "trainings": ["szkolenia"]
            }},
            "month_2_onwards": {{
                "milestones": [
                    {{"day": 60, "milestone": "opis", "success_criteria": "kryteria"}}
                ],
                "evaluation_criteria": ["kryteria oceny"]
            }},
            "resources": {{
                "documents": ["dokumenty do przeczytania"],
                "systems_access": ["systemy do skonfigurowania"],
                "contacts": ["ważne kontakty"]
            }},
            "success_metrics": [
                {{"metric": "nazwa", "target": "cel", "measured_at": "kiedy"}}
            ]
        }}
        """,
        agent=onboarding_specialist,
        expected_output="Onboarding plan in JSON format",
    )

    crew = Crew(
        agents=[onboarding_specialist],
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
                "onboarding_plan": parsed,
                "position": position,
                "duration_days": onboarding_duration_days,
            }
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "onboarding_plan": {"raw_content": result_text},
        "position": position,
        "duration_days": onboarding_duration_days,
    }


async def generate_welcome_email(
    employee_name: str,
    position: str,
    start_date: str,
    manager_name: str,
    company_name: str,
    first_day_info: str = "",
) -> dict:
    """Generate a welcome email for new employee.

    Args:
        employee_name: New employee's name
        position: Their position
        start_date: Start date
        manager_name: Manager's name
        company_name: Company name
        first_day_info: Additional first day information

    Returns:
        Dictionary with email content
    """
    llm = _get_llm()

    copywriter = Agent(
        role="HR Communication Specialist",
        goal="Pisać ciepłe i profesjonalne wiadomości powitalne",
        backstory="""Jesteś specjalistą od komunikacji HR. Piszesz wiadomości,
        które sprawiają, że nowi pracownicy czują się mile widziani.
        Twój styl jest profesjonalny, ale ciepły i ludzki.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""
        Napisz email powitalny dla nowego pracownika:

        - Imię: {employee_name}
        - Stanowisko: {position}
        - Data rozpoczęcia: {start_date}
        - Manager: {manager_name}
        - Firma: {company_name}
        - Dodatkowe info: {first_day_info or "brak"}

        Email powinien:
        1. Wyrażać radość z dołączenia do zespołu
        2. Potwierdzać szczegóły rozpoczęcia pracy
        3. Opisać co czeka w pierwszym dniu
        4. Zawierać kontakt do managera
        5. Budować pozytywne nastawienie

        Zwróć w formacie JSON:
        {{
            "subject": "temat emaila",
            "body": "treść emaila w HTML",
            "plain_text": "treść emaila bez formatowania"
        }}
        """,
        agent=copywriter,
        expected_output="Welcome email in JSON format",
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

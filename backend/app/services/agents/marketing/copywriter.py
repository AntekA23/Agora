from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


async def generate_marketing_copy(
    brief: str,
    copy_type: str = "ad",
    brand_voice: str = "profesjonalny",
    target_audience: str = "",
    language: str = "pl",
    max_length: int | None = None,
) -> dict:
    """Generate marketing copy using CrewAI agents."""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
    )

    copy_type_desc = {
        "ad": "tekst reklamowy",
        "email": "email marketingowy",
        "landing": "tekst na landing page",
        "slogan": "slogan/haslo reklamowe",
        "description": "opis produktu/uslugi",
    }.get(copy_type, "tekst reklamowy")

    length_instruction = f"Maksymalna dlugosc: {max_length} znakow." if max_length else ""

    copywriter = Agent(
        role="Copywriter",
        goal="Tworz przekonujace teksty marketingowe ktore sprzedaja",
        backstory=f"""Jestes doswiadczonym copywriterem specjalizujacym sie w polskim rynku.
        Znasz techniki perswazji i wiesz jak pisac teksty ktore konwertuja.
        Brand voice: {brand_voice}.
        Grupa docelowa: {target_audience or 'szeroka publicznosc'}.
        Zawsze piszesz po polsku.""",
        llm=llm,
        verbose=False,
    )

    marketing_manager = Agent(
        role="Marketing Manager",
        goal="Upewnij sie ze teksty sa zgodne z brandom i skuteczne",
        backstory=f"""Jestes Marketing Managerem z doswiadczeniem w polskich firmach.
        Oceniasz teksty pod katem skutecznosci i zgodnosci z brandom.
        Brand voice: {brand_voice}.""",
        llm=llm,
        verbose=False,
    )

    write_task = Task(
        description=f"""Napisz {copy_type_desc} na podstawie briefu:

BRIEF: {brief}

Wymagania:
1. Jezyk polski
2. Brand voice: {brand_voice}
3. Grupa docelowa: {target_audience or 'szeroka publicznosc'}
{length_instruction}

Stworz 2-3 warianty tekstu do wyboru.""",
        expected_output="2-3 warianty tekstu marketingowego",
        agent=copywriter,
    )

    review_task = Task(
        description="""Przejrzyj stworzone teksty i wybierz najlepszy wariant.
Uzasadnij krotko swoj wybor.
Wprowadz ewentualne poprawki do wybranego tekstu.""",
        expected_output="Najlepszy wariant tekstu z uzasadnieniem",
        agent=marketing_manager,
    )

    crew = Crew(
        agents=[copywriter, marketing_manager],
        tasks=[write_task, review_task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    return {
        "content": str(result),
        "copy_type": copy_type,
        "brief": brief,
    }

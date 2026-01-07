"""Copywriter agent with Tavily web search for SEO and market research."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.agents.tools.web_search import TavilySearchTool, TavilyCompetitorTool


async def generate_marketing_copy(
    brief: str,
    copy_type: str = "ad",
    brand_voice: str = "profesjonalny",
    target_audience: str = "",
    language: str = "pl",
    max_length: int | None = None,
) -> dict:
    """Generate marketing copy using CrewAI agents with Tavily research."""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
    )

    # Initialize Tavily tools
    search_tool = TavilySearchTool()
    competitor_tool = TavilyCompetitorTool()

    copy_type_desc = {
        "ad": "tekst reklamowy",
        "email": "email marketingowy",
        "landing": "tekst na landing page",
        "slogan": "slogan/haslo reklamowe",
        "description": "opis produktu/uslugi",
    }.get(copy_type, "tekst reklamowy")

    length_instruction = f"Maksymalna dlugosc: {max_length} znakow." if max_length else ""

    # SEO/Market Researcher
    seo_researcher = Agent(
        role="SEO & Market Researcher",
        goal="Zbadaj rynek i znajdz slowa kluczowe oraz inspiracje",
        backstory="""Jestes specjalista od SEO i badan rynku.
        Uzywasz narzedzi wyszukiwania aby znalezc:
        - Popularne slowa kluczowe w branzy
        - Co robi konkurencja
        - Jakie teksty najlepiej konwertuja
        Dostarczasz dane ktore pomagaja tworzyc skuteczniejsze teksty.""",
        llm=llm,
        tools=[search_tool, competitor_tool],
        verbose=False,
    )

    copywriter = Agent(
        role="Copywriter",
        goal="Tworz przekonujace teksty marketingowe ktore sprzedaja",
        backstory=f"""Jestes doswiadczonym copywriterem specjalizujacym sie w polskim rynku.
        Znasz techniki perswazji i wiesz jak pisac teksty ktore konwertuja.
        Wykorzystujesz dane z researchu do tworzenia lepszych tekstow.
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

    # Task 1: Research keywords and competitors
    research_task = Task(
        description=f"""Przeprowadz research dla tekstu marketingowego:

BRIEF: {brief}
TYP TEKSTU: {copy_type_desc}

Twoje zadania:
1. Uzyj 'tavily_search' aby znalezc popularne slowa kluczowe zwiazane z tematem
2. Uzyj 'tavily_competitor' aby sprawdzic jak konkurencja komunikuje podobne produkty/uslugi
3. Znajdz przykladowe teksty ktore dobrze konwertuja w tej branzy

Zwroc:
- SLOWA KLUCZOWE: 5-10 popularnych fraz do wykorzystania
- KONKURENCJA: jak konkurencja komunikuje podobne rzeczy
- BEST PRACTICES: co dziala w tego typu tekstach""",
        expected_output="Research ze slowami kluczowymi i analiza konkurencji",
        agent=seo_researcher,
    )

    # Task 2: Write copy based on research
    write_task = Task(
        description=f"""Na podstawie researchu napisz {copy_type_desc}:

BRIEF: {brief}

Wymagania:
1. Jezyk polski
2. Brand voice: {brand_voice}
3. Grupa docelowa: {target_audience or 'szeroka publicznosc'}
4. Wykorzystaj slowa kluczowe z researchu
5. Zastosuj techniki ktore dzialaja u konkurencji
{length_instruction}

Stworz 2-3 warianty tekstu do wyboru.
Dla kazdego wariantu:
- Oznacz wykorzystane slowa kluczowe
- Wyjasnij jaka technike perswazji zastosowales""",
        expected_output="2-3 warianty tekstu marketingowego z uzasadnieniem",
        agent=copywriter,
        context=[research_task],
    )

    # Task 3: Review and select best
    review_task = Task(
        description="""Przejrzyj stworzone teksty i wybierz najlepszy wariant.

Ocen kazdy wariant pod katem:
1. Wykorzystania slow kluczowych z researchu
2. Skutecznosci technik perswazji
3. Zgodnosci z brand voice
4. Potencjalu konwersji

Wybierz najlepszy wariant i uzasadnij krotko swoj wybor.
Wprowadz ewentualne poprawki do wybranego tekstu.

Zwroc w formacie:
- WYBRANY TEKST: [finalny tekst]
- UZASADNIENIE: [dlaczego ten wariant jest najlepszy]
- SLOWA KLUCZOWE: [wykorzystane slowa kluczowe]
- ALTERNATYWNE WARIANTY: [pozostale warianty jako backup]""",
        expected_output="Najlepszy wariant tekstu z uzasadnieniem",
        agent=marketing_manager,
        context=[research_task, write_task],
    )

    crew = Crew(
        agents=[seo_researcher, copywriter, marketing_manager],
        tasks=[research_task, write_task, review_task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    return {
        "content": str(result),
        "copy_type": copy_type,
        "brief": brief,
        "used_tavily": True,
    }

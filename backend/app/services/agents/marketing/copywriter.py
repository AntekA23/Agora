"""Copywriter agent with Tavily web search and memory for SEO and market research."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.agents.tools.web_search import TavilySearchTool, TavilyCompetitorTool
from app.services.agents.memory import memory_service
from app.services.agents.seasonal_context import build_seasonal_context


async def get_copywriter_memory_context(company_id: str, brief: str) -> str:
    """Get relevant memory context for copywriting task."""
    context_parts = []

    # Get similar successful tasks
    similar_tasks = await memory_service.get_similar_successful_tasks(
        company_id=company_id,
        brief=brief,
        agent="copywriter",
        limit=2,
    )

    if similar_tasks:
        context_parts.append("INSPIRACJE Z POPRZEDNICH UDANYCH TEKSTOW:")
        for task in similar_tasks:
            context_parts.append(f"- {task['content'][:300]}...")

    # Get company context
    company_context = await memory_service.get_company_context(
        company_id=company_id,
        query=brief,
        limit=3,
    )

    if company_context:
        context_parts.append(company_context)

    return "\n\n".join(context_parts) if context_parts else ""


async def generate_marketing_copy(
    brief: str,
    copy_type: str = "ad",
    brand_voice: str = "profesjonalny",
    target_audience: str = "",
    language: str = "pl",
    max_length: int | None = None,
    company_id: str = "",
    brand_context: str = "",
) -> dict:
    """Generate marketing copy using CrewAI agents with Tavily research, memory, and brand context."""

    # Get memory context if company_id provided
    memory_context = ""
    if company_id:
        try:
            memory_context = await get_copywriter_memory_context(company_id, brief)
        except Exception:
            pass  # Memory is optional

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

    # Build seasonal context
    seasonal_context = build_seasonal_context()

    # Build comprehensive brand info from context
    brand_info = ""
    if brand_context:
        brand_info = f"""

        SZCZEGOLOWY KONTEKST MARKI:
        {brand_context}

        {seasonal_context}

        Wykorzystaj informacje o produktach, bolaczkach klientow i przewagach konkurencyjnych.
        Dostosuj tresc do aktualnej pory roku i nadchodzacych okazji!"""
    else:
        # Fallback for backward compatibility
        brand_info = f"""
        Brand voice: {brand_voice}.
        Grupa docelowa: {target_audience or 'szeroka publicznosc'}.

        {seasonal_context}"""

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

    # Build memory context for agent
    memory_info = ""
    if memory_context:
        memory_info = f"""

        PAMIEC I DOSWIADCZENIE:
        {memory_context}

        Wykorzystaj te informacje aby tworzyc lepsze teksty."""

    copywriter = Agent(
        role="Copywriter",
        goal="Tworz przekonujace teksty marketingowe ktore sprzedaja",
        backstory=f"""Jestes doswiadczonym copywriterem specjalizujacym sie w polskim rynku.
        Znasz techniki perswazji i wiesz jak pisac teksty ktore konwertuja.
        Wykorzystujesz dane z researchu do tworzenia lepszych tekstow.{brand_info}{memory_info}
        Zawsze piszesz po polsku.""",
        llm=llm,
        verbose=False,
    )

    marketing_manager = Agent(
        role="Marketing Manager",
        goal="Upewnij sie ze teksty sa zgodne z brandom i skuteczne",
        backstory=f"""Jestes Marketing Managerem z doswiadczeniem w polskich firmach.
        Oceniasz teksty pod katem skutecznosci i zgodnosci z brandom.{brand_info}""",
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

{'WAZNE: Masz dostep do szczegolowego kontekstu marki w swoim backstory. Wykorzystaj informacje o produktach, bolaczkach klientow, ich celach i przewagach konkurencyjnych.' if brand_context else ''}

Wymagania:
1. Jezyk polski
2. Styl zgodny z tonem komunikacji z kontekstu marki
3. Adresuj bolaczki grupy docelowej (jesli okreslone w kontekscie)
4. Podkresl jak produkt/usluga realizuje cele klientow
5. Wykorzystaj slowa kluczowe z researchu
6. Uzywaj preferowanych slow i unikaj slow zabronionych (jesli okreslone w kontekscie)
7. Zastosuj techniki ktore dzialaja u konkurencji
8. Wykorzystaj USP produktow/uslug (jesli dostepne w kontekscie)
9. DOSTOSUJ tresc do PORY ROKU i nadchodzacych swiat/okazji z kontekstu czasowego!
{length_instruction}

Stworz 2-3 warianty tekstu do wyboru.
Dla kazdego wariantu:
- Oznacz wykorzystane slowa kluczowe
- Wyjasnij jaka technike perswazji zastosowales
- Wskazac ktore bolaczki/cele klienta adresujesz""",
        expected_output="2-3 warianty tekstu marketingowego z uzasadnieniem",
        agent=copywriter,
        context=[research_task],
    )

    # Task 3: Review and select best
    review_task = Task(
        description=f"""Przejrzyj stworzone teksty i wybierz najlepszy wariant.

Ocen kazdy wariant pod katem:
1. Wykorzystania slow kluczowych z researchu
2. Skutecznosci technik perswazji
3. Zgodnosci ze stylem komunikacji marki
4. Potencjalu konwersji
5. {'Adresowania bolaczek i celow klientow z kontekstu marki' if brand_context else 'Trafnosci do grupy docelowej'}
6. {'Nie uzyto slow zabronionych (jesli okreslone w kontekscie)' if brand_context else ''}
7. {'Wykorzystania USP produktow/uslug' if brand_context else ''}
8. SEZONOWOSC - czy tresc jest dostosowana do aktualnej pory roku i nadchodzacych okazji?

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
        "used_memory": bool(memory_context),
        "used_brand_context": bool(brand_context),
    }

"""Instagram content creation agent with Tavily web search and memory capabilities."""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.agents.tools.web_search import TavilySearchTool, TavilyTrendsTool
from app.services.agents.memory import memory_service, MemoryType


async def get_memory_context(company_id: str, brief: str) -> str:
    """Get relevant memory context for the task."""
    context_parts = []

    # Get similar successful tasks
    similar_tasks = await memory_service.get_similar_successful_tasks(
        company_id=company_id,
        brief=brief,
        agent="instagram_specialist",
        limit=2,
    )

    if similar_tasks:
        context_parts.append("INSPIRACJE Z POPRZEDNICH UDANYCH POSTOW:")
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


def create_instagram_crew(
    brief: str,
    brand_voice: str = "profesjonalny",
    target_audience: str = "",
    language: str = "pl",
    include_hashtags: bool = True,
    post_type: str = "post",
    memory_context: str = "",
    brand_context: str = "",
) -> Crew:
    """Create a CrewAI crew for Instagram content creation with web research."""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
    )

    # Initialize Tavily tools
    search_tool = TavilySearchTool()
    trends_tool = TavilyTrendsTool()

    # Content Researcher - uses Tavily to research trends
    content_researcher = Agent(
        role="Content Researcher",
        goal="Zbadaj aktualne trendy i znajdz inspiracje dla contentu",
        backstory="""Jestes specjalista od researchu social media.
        Uzywasz narzedzi do wyszukiwania aby znalezc:
        - Aktualne trendy w branzy
        - Popularne hashtagi
        - Co dziala u konkurencji
        Dostarczasz dane ktore pomagaja tworzyc lepszy content.""",
        llm=llm,
        tools=[search_tool, trends_tool],
        verbose=False,
    )

    # Build comprehensive brand info from context
    brand_info = ""
    if brand_context:
        brand_info = f"""

        SZCZEGOLOWY KONTEKST MARKI:
        {brand_context}

        Wykorzystaj te informacje przy tworzeniu i ocenie contentu."""
    else:
        # Fallback for backward compatibility
        brand_info = f"""
        Brand voice firmy: {brand_voice}.
        Grupa docelowa: {target_audience or 'szeroka publicznosc'}."""

    # Marketing Manager - oversees and approves content
    marketing_manager = Agent(
        role="Marketing Manager",
        goal="Nadzoruj tworzenie contentu i upewnij sie ze jest zgodny z brandom",
        backstory=f"""Jestes doswiadczonym Marketing Managerem w polskiej firmie.
        Znasz sie na social media i wiesz co dziala na Instagramie.{brand_info}
        Zawsze odpowiadasz po polsku.""",
        llm=llm,
        verbose=False,
    )

    # Build memory context for agent
    memory_info = ""
    if memory_context:
        memory_info = f"""

        PAMIEC I DOSWIADCZENIE:
        {memory_context}

        Wykorzystaj te informacje aby tworzyc lepszy content."""

    # Instagram Specialist - creates the actual content
    instagram_specialist = Agent(
        role="Instagram Specialist",
        goal="Tworz angazujace posty na Instagram ktore przyciagaja uwage",
        backstory=f"""Jestes specjalista od Instagrama z wieloletnim doswiadczeniem.
        Wiesz jak pisac teksty ktore generuja zaangazowanie.
        Korzystasz z danych z researchu aby tworzyc lepszy content.{brand_info}{memory_info}
        Zawsze piszesz po polsku.""",
        llm=llm,
        verbose=False,
    )

    # Define the content type
    content_type_desc = {
        "post": "standardowy post na feed",
        "story": "krotka tresc na Instagram Story",
        "reel": "scenariusz dla krotkiego video Reels",
        "carousel": "seria slajdow karuzeli (3-5 slajdow)",
    }.get(post_type, "standardowy post na feed")

    # Task 1: Research trends and hashtags
    research_task = Task(
        description=f"""Przeprowadz research dla posta na Instagram:

BRIEF: {brief}
BRANZA/TEMAT: {brief[:50]}

Twoje zadania:
1. Uzyj narzedzia 'tavily_trends' aby znalezc aktualne trendy zwiazane z tematem
2. Uzyj narzedzia 'tavily_search' aby znalezc popularne hashtagi dla tego tematu
3. Sprawdz co dziala w social media w tej branzy

Zwroc:
- TRENDY: 3-5 aktualnych trendow
- HASHTAGI: 10-15 popularnych hashtagow
- INSPIRACJE: 2-3 pomysly na content""",
        expected_output="Research z trendami, hashtagami i inspiracjami",
        agent=content_researcher,
    )

    # Build hashtag instruction based on brand context
    hashtag_instruction = "Bez hashtagow"
    if include_hashtags:
        if brand_context and "Hashtagi firmowe:" in brand_context:
            hashtag_instruction = "Uzyj hashtagow firmowych z kontekstu marki oraz dodaj 3-5 hashtagow z researchu"
        else:
            hashtag_instruction = "Uzyj hashtagow z researchu (wybierz 5-10 najlepszych)"

    # Task 2: Create content based on research
    create_content_task = Task(
        description=f"""Na podstawie researchu stworz {content_type_desc} na Instagram:

BRIEF: {brief}

{'WAZNE: Masz dostep do szczegolowego kontekstu marki w swoim backstory. Wykorzystaj informacje o produktach, stylach komunikacji i hashtagach firmowych.' if brand_context else ''}

Wymagania:
1. Tekst musi byc w jezyku polskim
2. Tekst musi byc angazujacy i zgodny ze stylem komunikacji z kontekstu marki
3. {hashtag_instruction}
4. Uwzglednij grupe docelowa z kontekstu marki
5. Wykorzystaj trendy znalezione w researchu
6. Jesli masz informacje o produktach/uslugach firmy, mozesz je naturalnie wplatac w tresc
7. Uzywaj preferowanych slow i unikaj slow zabronionych (jesli okreslone w kontekscie)
8. Zaproponuj najlepszy czas publikacji

WAZNE - OPIS GRAFIKI:
Grafika bedzie GENEROWANA PRZEZ AI (model obrazkowy), wiec:
- NIGDY nie sugeruj zrzutow ekranu, interfejsow aplikacji, logo firmy
- NIGDY nie sugeruj konkretnych zdjec produktow ktorych AI nie zna
- NIGDY nie sugeruj zdjec prawdziwych osob (celebrytow, pracownikow)
- ZAMIAST TEGO opisz: abstrakcyjne koncepcje, lifestyle, emocje, metafory wizualne
- Przyklad ZLY: "zrzut ekranu aplikacji Dario z interfejsem"
- Przyklad DOBRY: "usmiechniete dziecko podczas zabawy edukacyjnej, ciepłe swiatlo, radosna atmosfera"
- Opis musi byc w jezyku ANGIELSKIM (dla modelu AI)

Zwroc wynik w formacie:
- TEKST POSTU: [tekst]
- HASHTAGI: [hashtagi jesli wymagane]
- CZAS PUBLIKACJI: [sugerowany czas]
- OPIS GRAFIKI: [opis w jezyku angielskim, bez elementow niemozliwych do wygenerowania]
- WYKORZYSTANE TRENDY: [jakie trendy zostaly wykorzystane]""",
        expected_output="Gotowy post na Instagram z tekstem, hashtagami i sugestiami",
        agent=instagram_specialist,
        context=[research_task],
    )

    # Task 3: Review and approve
    review_task = Task(
        description=f"""Przejrzyj stworzony content pod katem:
1. Zgodnosci ze stylem komunikacji marki (formalnosc, ton, uzywane slowa)
2. Atrakcyjnosci dla grupy docelowej okreslonej w kontekscie marki
3. Poprawnosci jezykowej
4. Wykorzystania trendow z researchu
5. Potencjalu wiralowego
6. {'Uzyte zostaly hashtagi firmowe marki' if brand_context and 'Hashtagi firmowe:' in brand_context else 'Hashtagi sa odpowiednie'}
7. Nie uzyto slow zabronionych (jesli okreslone w kontekscie)

KRYTYCZNE - WERYFIKACJA OPISU GRAFIKI:
Grafika bedzie generowana przez AI, wiec ODRZUC opisy zawierajace:
- Zrzuty ekranu, interfejsy aplikacji, dashboardy
- Logo, nazwy marek widoczne na grafice
- Konkretne produkty ktorych AI nie zna
- Prawdziwe osoby (celebryci, pracownicy)
Jesli opis zawiera takie elementy, PRZEPISZ go na opis mozliwy do wygenerowania.
Opis MUSI byc po angielsku.

Jesli wszystko jest OK, zatwierdz content.
Jesli cos wymaga poprawy, wprowadz korekty.

Zwroc finalny, zatwierdzony content w formacie:
- TEKST POSTU: [tekst]
- HASHTAGI: [hashtagi]
- CZAS PUBLIKACJI: [czas]
- OPIS GRAFIKI: [opis po angielsku, bez niemozliwych elementow]""",
        expected_output="Zatwierdzony post gotowy do publikacji",
        agent=marketing_manager,
        context=[research_task, create_content_task],
    )

    crew = Crew(
        agents=[content_researcher, instagram_specialist, marketing_manager],
        tasks=[research_task, create_content_task, review_task],
        process=Process.sequential,
        verbose=False,
    )

    return crew


async def generate_instagram_post(
    brief: str,
    brand_voice: str = "profesjonalny",
    target_audience: str = "",
    language: str = "pl",
    include_hashtags: bool = True,
    post_type: str = "post",
    company_id: str = "",
    brand_context: str = "",
) -> dict:
    """Generate Instagram post using CrewAI agents with Tavily research, memory, and brand context."""

    # Get memory context if company_id provided
    memory_context = ""
    if company_id:
        try:
            memory_context = await get_memory_context(company_id, brief)
        except Exception:
            pass  # Memory is optional, continue without it

    crew = create_instagram_crew(
        brief=brief,
        brand_voice=brand_voice,
        target_audience=target_audience,
        language=language,
        include_hashtags=include_hashtags,
        post_type=post_type,
        memory_context=memory_context,
        brand_context=brand_context,
    )

    # Run the crew (this is synchronous in CrewAI, we wrap it)
    result = crew.kickoff()

    # Parse the result
    result_text = str(result)

    # Extract sections from the result
    output = {
        "content": result_text,
        "post_type": post_type,
        "brief": brief,
        "used_tavily": True,
        "used_memory": bool(memory_context),
        "used_brand_context": bool(brand_context),
    }

    # Try to extract structured data
    if "TEKST POSTU:" in result_text:
        parts = result_text.split("TEKST POSTU:")
        if len(parts) > 1:
            text_part = parts[1].split("HASHTAGI:")[0] if "HASHTAGI:" in parts[1] else parts[1]
            output["post_text"] = text_part.strip()

    if "HASHTAGI:" in result_text:
        hashtag_part = result_text.split("HASHTAGI:")[1]
        hashtag_part = hashtag_part.split("CZAS")[0] if "CZAS" in hashtag_part else hashtag_part
        output["hashtags"] = hashtag_part.strip()

    if "CZAS PUBLIKACJI:" in result_text:
        time_part = result_text.split("CZAS PUBLIKACJI:")[1]
        time_part = time_part.split("OPIS")[0] if "OPIS" in time_part else time_part
        output["suggested_time"] = time_part.strip()

    if "OPIS GRAFIKI:" in result_text:
        image_part = result_text.split("OPIS GRAFIKI:")[1]
        # Handle case where there might be more sections after
        for delimiter in ["WYKORZYSTANE", "---", "\n\n\n"]:
            if delimiter in image_part:
                image_part = image_part.split(delimiter)[0]
                break
        output["image_prompt"] = image_part.strip()

    return output

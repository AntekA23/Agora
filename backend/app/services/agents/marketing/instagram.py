from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


def create_instagram_crew(
    brief: str,
    brand_voice: str = "profesjonalny",
    target_audience: str = "",
    language: str = "pl",
    include_hashtags: bool = True,
    post_type: str = "post",
) -> Crew:
    """Create a CrewAI crew for Instagram content creation."""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
    )

    # Marketing Manager - oversees and approves content
    marketing_manager = Agent(
        role="Marketing Manager",
        goal="Nadzoruj tworzenie contentu i upewnij sie ze jest zgodny z brandom",
        backstory=f"""Jestes doswiadczonym Marketing Managerem w polskiej firmie.
        Znasz sie na social media i wiesz co dziala na Instagramie.
        Brand voice firmy: {brand_voice}.
        Grupa docelowa: {target_audience or 'szeroka publicznosc'}.
        Zawsze odpowiadasz po polsku.""",
        llm=llm,
        verbose=False,
    )

    # Instagram Specialist - creates the actual content
    instagram_specialist = Agent(
        role="Instagram Specialist",
        goal="Tworz angazujace posty na Instagram ktore przyciagaja uwage",
        backstory=f"""Jestes specjalista od Instagrama z wieloletnim doswiadczeniem.
        Wiesz jak pisac teksty ktore generuja zaangazowanie.
        Znasz trendy i algorytm Instagrama.
        Brand voice: {brand_voice}.
        Grupa docelowa: {target_audience or 'szeroka publicznosc'}.
        Zawsze piszesz po polsku.""",
        llm=llm,
        verbose=False,
    )

    # Define the content type
    content_type_desc = {
        "post": "standardowy post na feed",
        "story": "krotka tresc na Instagram Story",
        "reel": "scenariusz dla krotokiego video Reels",
        "carousel": "seria slajdow karuzeli (3-5 slajdow)",
    }.get(post_type, "standardowy post na feed")

    # Task for Instagram Specialist
    create_content_task = Task(
        description=f"""Stworz {content_type_desc} na Instagram na podstawie briefu:

BRIEF: {brief}

Wymagania:
1. Tekst musi byc w jezyku polskim
2. Tekst musi byc angazujacy i zgodny z brand voice: {brand_voice}
3. {'Dodaj odpowiednie hashtagi (5-10)' if include_hashtags else 'Bez hashtagow'}
4. Uwzglednij grupe docelowa: {target_audience or 'szeroka publicznosc'}
5. Zaproponuj najlepszy czas publikacji

Zwroc wynik w formacie:
- TEKST POSTU: [tekst]
- HASHTAGI: [hashtagi jesli wymagane]
- CZAS PUBLIKACJI: [sugerowany czas]
- OPIS GRAFIKI: [krotki opis jaka grafika pasowałaby do postu]""",
        expected_output="Gotowy post na Instagram z tekstem, hashtagami i sugestiami",
        agent=instagram_specialist,
    )

    # Task for Marketing Manager to review
    review_task = Task(
        description=f"""Przejrzyj stworzony content pod katem:
1. Zgodnosci z brand voice: {brand_voice}
2. Atrakcyjnosci dla grupy docelowej: {target_audience or 'szeroka publicznosc'}
3. Poprawnosci jezykowej
4. Potencjalu wiralowego

Jesli wszystko jest OK, zatwierdz content.
Jesli cos wymaga poprawy, wprowadz korekty.

Zwroc finalny, zatwierdzony content.""",
        expected_output="Zatwierdzony post gotowy do publikacji",
        agent=marketing_manager,
    )

    crew = Crew(
        agents=[instagram_specialist, marketing_manager],
        tasks=[create_content_task, review_task],
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
) -> dict:
    """Generate Instagram post using CrewAI agents."""

    crew = create_instagram_crew(
        brief=brief,
        brand_voice=brand_voice,
        target_audience=target_audience,
        language=language,
        include_hashtags=include_hashtags,
        post_type=post_type,
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
        output["image_prompt"] = image_part.strip()

    return output

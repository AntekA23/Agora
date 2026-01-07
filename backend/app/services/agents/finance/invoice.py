from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


async def generate_invoice_draft(
    client_name: str,
    client_address: str,
    items: list[dict],
    notes: str = "",
    language: str = "pl",
) -> dict:
    """Generate invoice draft using CrewAI agents."""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.3,
    )

    # Format items for the prompt
    items_text = "\n".join([
        f"- {item.get('name', 'Usluga')}: {item.get('quantity', 1)} x {item.get('price', 0)} PLN"
        for item in items
    ])

    total = sum(
        item.get('quantity', 1) * item.get('price', 0)
        for item in items
    )
    vat = total * 0.23
    gross = total + vat

    finance_manager = Agent(
        role="Finance Manager",
        goal="Przygotuj profesjonalna fakture zgodna z polskimi przepisami",
        backstory="""Jestes doswiadczonym ksiegowym specjalizujacym sie w polskich firmach.
        Znasz przepisy dotyczace fakturowania i VAT.
        Zawsze dbasz o poprawnosc danych i profesjonalny wyglad dokumentow.""",
        llm=llm,
        verbose=False,
    )

    invoice_worker = Agent(
        role="Invoice Specialist",
        goal="Stworz kompletny draft faktury",
        backstory="""Jestes specjalista od fakturowania.
        Tworzysz czytelne i profesjonalne faktury.
        Znasz wszystkie wymagane pola faktury VAT.""",
        llm=llm,
        verbose=False,
    )

    create_invoice_task = Task(
        description=f"""Przygotuj draft faktury VAT z nastepujacymi danymi:

NABYWCA:
Nazwa: {client_name}
Adres: {client_address}

POZYCJE:
{items_text}

SUMA NETTO: {total:.2f} PLN
VAT (23%): {vat:.2f} PLN
SUMA BRUTTO: {gross:.2f} PLN

UWAGI: {notes or 'Brak'}

Stworz profesjonalny draft faktury zawierajacy:
1. Wszystkie wymagane dane (miejsce na dane sprzedawcy)
2. Numer faktury (placeholder)
3. Date wystawienia i sprzedazy
4. Termin platnosci (14 dni)
5. Numer konta bankowego (placeholder)
6. Podsumowanie z VAT

Format wynikowy powinien byc czytelny i gotowy do uzupelnienia.""",
        expected_output="Kompletny draft faktury VAT",
        agent=invoice_worker,
    )

    review_task = Task(
        description="""Sprawdz draft faktury pod katem:
1. Poprawnosci obliczen (netto, VAT, brutto)
2. Kompletnosci wymaganych pol
3. Zgodnosci z polskimi przepisami
4. Profesjonalnego formatowania

Wprowadz ewentualne poprawki i zatwierdz finalny draft.""",
        expected_output="Zatwierdzony draft faktury",
        agent=finance_manager,
    )

    crew = Crew(
        agents=[invoice_worker, finance_manager],
        tasks=[create_invoice_task, review_task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    return {
        "content": str(result),
        "client_name": client_name,
        "client_address": client_address,
        "items": items,
        "total_net": total,
        "vat": vat,
        "total_gross": gross,
        "notes": notes,
    }


async def analyze_cashflow(
    income: list[dict],
    expenses: list[dict],
    period: str = "miesiac",
    language: str = "pl",
) -> dict:
    """Analyze cashflow using CrewAI agents."""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.4,
    )

    # Format data
    income_text = "\n".join([
        f"- {item.get('description', 'Przychod')}: {item.get('amount', 0)} PLN ({item.get('date', '')})"
        for item in income
    ])

    expenses_text = "\n".join([
        f"- {item.get('description', 'Wydatek')}: {item.get('amount', 0)} PLN ({item.get('category', 'inne')})"
        for item in expenses
    ])

    total_income = sum(item.get('amount', 0) for item in income)
    total_expenses = sum(item.get('amount', 0) for item in expenses)
    balance = total_income - total_expenses

    cashflow_analyst = Agent(
        role="Cashflow Analyst",
        goal="Analizuj przeplywy pieniezne i identyfikuj trendy",
        backstory="""Jestes analitykiem finansowym specjalizujacym sie w malych firmach.
        Potrafisz wyciagac wnioski z danych finansowych i dawac praktyczne rekomendacje.
        Komunikujesz sie jasno i przystepnie.""",
        llm=llm,
        verbose=False,
    )

    analyze_task = Task(
        description=f"""Przeanalizuj przeplywy pieniezne za {period}:

PRZYCHODY ({total_income:.2f} PLN):
{income_text or 'Brak danych'}

WYDATKI ({total_expenses:.2f} PLN):
{expenses_text or 'Brak danych'}

BILANS: {balance:.2f} PLN

Przygotuj analize zawierajaca:
1. Podsumowanie sytuacji finansowej
2. Glowne zrodla przychodow
3. Najwieksze kategorie wydatkow
4. Trendy i wzorce (jesli widoczne)
5. 3-5 konkretnych rekomendacji

Pisz zwiezle i praktycznie.""",
        expected_output="Analiza cashflow z rekomendacjami",
        agent=cashflow_analyst,
    )

    crew = Crew(
        agents=[cashflow_analyst],
        tasks=[analyze_task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    return {
        "content": str(result),
        "period": period,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance,
    }

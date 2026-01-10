"""Terms Generator Agent - Regulaminy zgodne z polskim prawem.

Generator dokumentów prawnych zgodny z:
- Ustawą o świadczeniu usług drogą elektroniczną (UŚUDE) z 18.07.2002
- Ustawą o prawach konsumenta z 30.05.2014
- Kodeksem cywilnym (KC)
- RODO (Rozporządzenie 2016/679)

Autor: Agora Platform
"""

import json
import re
from datetime import datetime
from typing import Optional

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.core.config import settings


# =============================================================================
# POLSKIE PODSTAWY PRAWNE
# =============================================================================

POLISH_ECOMMERCE_LAW = {
    "uśude": {
        "name": "Ustawa o świadczeniu usług drogą elektroniczną",
        "date": "18 lipca 2002 r.",
        "dz_u": "Dz.U. 2002 nr 144 poz. 1204",
        "key_articles": {
            "definicje": "Art. 2 - definicje usługodawcy, usługobiorcy, usługi elektronicznej",
            "obowiązki_informacyjne": "Art. 5 - dane usługodawcy (nazwa, adres, NIP, kontakt)",
            "regulamin": "Art. 8 - obowiązkowe elementy regulaminu",
            "zakaz_spamu": "Art. 10 - zakaz niezamówionej informacji handlowej",
            "treści_bezprawne": "Art. 8 ust. 3 pkt 2 - zakaz treści o charakterze bezprawnym",
            "odpowiedzialność": "Art. 12-15 - wyłączenia odpowiedzialności providera",
            "reklamacje": "Art. 8 ust. 3 pkt 4 - tryb postępowania reklamacyjnego",
        },
        "obowiązkowe_elementy_regulaminu": [
            "rodzaje i zakres usług świadczonych drogą elektroniczną",
            "warunki świadczenia usług drogą elektroniczną (wymagania techniczne, zakaz treści bezprawnych)",
            "warunki zawierania i rozwiązywania umów o świadczenie usług",
            "tryb postępowania reklamacyjnego",
        ],
    },
    "ustawa_konsumencka": {
        "name": "Ustawa o prawach konsumenta",
        "date": "30 maja 2014 r.",
        "dz_u": "Dz.U. 2014 poz. 827",
        "key_articles": {
            "obowiązki_informacyjne": "Art. 12 - obowiązki informacyjne przed zawarciem umowy",
            "prawo_odstąpienia": "Art. 27 - 14 dni na odstąpienie bez podania przyczyny",
            "termin_odstąpienia": "Art. 28-30 - bieg terminu do odstąpienia",
            "forma_odstąpienia": "Art. 30 - oświadczenie o odstąpieniu",
            "wzór_formularza": "Załącznik nr 2 - wzór formularza odstąpienia",
            "skutki_odstąpienia": "Art. 31-33 - zwrot płatności, kosztów dostawy",
            "wyjątki_od_odstąpienia": "Art. 38 - umowy wyłączone z prawa odstąpienia",
            "reklamacja_rękojmia": "Art. 556-576 KC - rękojmia za wady",
            "gwarancja": "Art. 577-581 KC - gwarancja jakości",
        },
    },
    "kodeks_cywilny": {
        "name": "Kodeks cywilny",
        "key_articles": {
            "umowa_elektroniczna": "Art. 66¹-66² KC - oferta elektroniczna",
            "forma_dokumentowa": "Art. 77² KC - forma dokumentowa",
            "wzorce_umowne": "Art. 384-385⁴ KC - wzorce umów, klauzule abuzywne",
            "rękojmia": "Art. 556-576 KC - rękojmia za wady",
        },
    },
}

# Wyjątki od prawa odstąpienia (Art. 38 ustawy o prawach konsumenta)
WITHDRAWAL_EXCEPTIONS = [
    {
        "article": "Art. 38 pkt 1",
        "description": "usługi, jeżeli przedsiębiorca wykonał w pełni usługę za wyraźną zgodą konsumenta",
        "example": "konsultacja online, dostęp do webinaru",
    },
    {
        "article": "Art. 38 pkt 3",
        "description": "rzeczy nieprefabrykowane, wyprodukowane według specyfikacji konsumenta",
        "example": "personalizowane produkty, druk na żądanie",
    },
    {
        "article": "Art. 38 pkt 4",
        "description": "rzeczy ulegające szybkiemu zepsuciu lub mające krótki termin przydatności",
        "example": "żywność, kwiaty cięte",
    },
    {
        "article": "Art. 38 pkt 5",
        "description": "rzeczy dostarczane w zapieczętowanym opakowaniu, jeżeli opakowanie zostało otwarte",
        "example": "kosmetyki, suplementy diety po otwarciu",
    },
    {
        "article": "Art. 38 pkt 9",
        "description": "nagrania dźwiękowe/wizualne/programy komputerowe w zapieczętowanym opakowaniu, jeżeli otwarto",
        "example": "płyty CD/DVD, gry pudełkowe po otwarciu",
    },
    {
        "article": "Art. 38 pkt 12",
        "description": "usługi hotelarskie, przewóz rzeczy, wynajem samochodów, gastronomia, wypoczynek - jeżeli określono termin",
        "example": "rezerwacja hotelu na konkretny termin",
    },
    {
        "article": "Art. 38 pkt 13",
        "description": "treści cyfrowe niedostarczane na nośniku materialnym, jeżeli spełnianie świadczenia rozpoczęto za zgodą konsumenta",
        "example": "e-booki, kursy online, oprogramowanie do pobrania",
    },
]

# Wymagane informacje dla konsumenta (Art. 12 ustawy o prawach konsumenta)
REQUIRED_CONSUMER_INFO = [
    "główne cechy świadczenia z uwzględnieniem przedmiotu świadczenia",
    "dane identyfikujące przedsiębiorcę (firma, NIP, adres, telefon, email)",
    "adres przedsiębiorstwa i ewentualnie adres do składania reklamacji",
    "łączna cena lub wynagrodzenie wraz z podatkami",
    "sposób i termin zapłaty",
    "sposób i termin spełnienia świadczenia, procedura reklamacyjna",
    "sposób i termin wykonania prawa odstąpienia oraz wzór formularza odstąpienia",
    "koszty zwrotu rzeczy w przypadku odstąpienia, które ponosi konsument",
    "brak prawa odstąpienia lub okoliczności jego utraty (jeśli dotyczy)",
    "obowiązek przedsiębiorcy dostarczenia rzeczy bez wad",
    "istnienie odpowiedzialności z tytułu rękojmi",
    "treść usług posprzedażnych i gwarancji (jeśli dotyczy)",
    "czas trwania umowy lub sposób i przesłanki wypowiedzenia",
    "minimalny czas trwania zobowiązań konsumenta (jeśli dotyczy)",
    "wysokość kaucji lub innych gwarancji finansowych (jeśli dotyczy)",
    "funkcjonalność treści cyfrowych oraz techniczne środki ich ochrony (jeśli dotyczy)",
    "mające znaczenie interoperacyjności treści cyfrowych (jeśli dotyczy)",
    "możliwość skorzystania z pozasądowych sposobów rozpatrywania reklamacji",
]

# Wzór formularza odstąpienia (Załącznik nr 2 do ustawy)
WITHDRAWAL_FORM_TEMPLATE = """
WZÓR FORMULARZA ODSTĄPIENIA OD UMOWY
(formularz ten należy wypełnić i odesłać tylko w przypadku chęci odstąpienia od umowy)

Adresat: [NAZWA PRZEDSIĘBIORCY]
[ADRES PRZEDSIĘBIORCY]
[EMAIL PRZEDSIĘBIORCY]

Ja/My(*) niniejszym informuję/informujemy(*) o moim/naszym(*) odstąpieniu od umowy sprzedaży
następujących rzeczy(*) / umowy dostawy następujących rzeczy(*) / umowy o dzieło polegającej
na wykonaniu następujących rzeczy(*) / o świadczenie następującej usługi(*)

Data zawarcia umowy(*)/odbioru(*):

Imię i nazwisko konsumenta(-ów):

Adres konsumenta(-ów):

Podpis konsumenta(-ów) (tylko jeżeli formularz jest przesyłany w wersji papierowej):

Data:

(*) Niepotrzebne skreślić.
"""


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,  # Niższa temperatura dla dokumentów prawnych
        api_key=settings.OPENAI_API_KEY,
    )


def _get_current_date() -> str:
    """Get current date in Polish format."""
    months = [
        "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
        "lipca", "sierpnia", "września", "października", "listopada", "grudnia"
    ]
    now = datetime.now()
    return f"{now.day} {months[now.month - 1]} {now.year} r."


# =============================================================================
# GENERATOR REGULAMINU
# =============================================================================

async def generate_terms_of_service(
    # Dane usługodawcy (Art. 5 UŚUDE)
    company_name: str,
    company_address: str,
    company_nip: str = "",
    company_regon: str = "",
    company_krs: str = "",
    contact_email: str = "",
    contact_phone: str = "",

    # Dane o usłudze
    service_type: str = "saas",
    service_description: str = "",
    website_url: str = "",

    # Model biznesowy
    pricing_model: str = "",
    payment_terms: str = "",
    subscription_based: bool = False,
    free_trial: bool = False,
    free_trial_days: int = 14,

    # Typ klientów
    b2b_only: bool = False,

    # Polityki
    refund_policy: str = "",

    # Treści cyfrowe (Art. 38 pkt 13)
    digital_content: bool = False,
    digital_content_description: str = "",
) -> dict:
    """Generuje regulamin świadczenia usług drogą elektroniczną.

    Zgodny z:
    - Art. 8 ustawy o świadczeniu usług drogą elektroniczną
    - Ustawą o prawach konsumenta (jeśli B2C)
    - Art. 384-385⁴ Kodeksu cywilnego (wzorce umowne)

    Args:
        company_name: Pełna nazwa firmy
        company_address: Adres siedziby
        company_nip: NIP
        company_regon: REGON
        company_krs: Numer KRS (jeśli dotyczy)
        contact_email: Email kontaktowy
        contact_phone: Telefon kontaktowy
        service_type: Typ usługi (saas, ecommerce, marketplace, consulting, agency)
        service_description: Opis usługi
        website_url: Adres strony internetowej
        pricing_model: Model cenowy
        payment_terms: Warunki płatności
        subscription_based: Czy model subskrypcyjny
        free_trial: Czy oferowany okres próbny
        free_trial_days: Liczba dni okresu próbnego
        b2b_only: Czy tylko dla firm (B2B)
        refund_policy: Polityka zwrotów
        digital_content: Czy dostarcza treści cyfrowe
        digital_content_description: Opis treści cyfrowych

    Returns:
        Słownik z pełnym regulaminem i metadanymi
    """
    llm = _get_llm()

    # Mapowanie typów usług
    service_types = {
        "saas": "oprogramowanie jako usługa (SaaS)",
        "ecommerce": "sprzedaż towarów przez internet",
        "marketplace": "platforma pośrednictwa handlowego",
        "consulting": "usługi doradcze online",
        "agency": "usługi agencyjne",
        "education": "usługi edukacyjne online",
    }
    service_type_pl = service_types.get(service_type.lower(), service_type)

    # Przygotuj informacje o wyjątkach od odstąpienia
    applicable_exceptions = []
    if digital_content:
        applicable_exceptions.append(WITHDRAWAL_EXCEPTIONS[6])  # Art. 38 pkt 13
    if service_type.lower() == "saas":
        applicable_exceptions.append(WITHDRAWAL_EXCEPTIONS[0])  # Art. 38 pkt 1

    exceptions_text = "\n".join([
        f"- {exc['article']}: {exc['description']} (np. {exc['example']})"
        for exc in applicable_exceptions
    ]) if applicable_exceptions else "Brak szczególnych wyjątków."

    legal_writer = Agent(
        role="Specjalista ds. Regulaminów E-commerce",
        goal="Tworzyć regulaminy w pełni zgodne z polskim prawem e-commerce",
        backstory=f"""Jesteś doświadczonym prawnikiem specjalizującym się w prawie
        internetowym i e-commerce w Polsce. Masz dogłębną znajomość:

        1. Ustawy o świadczeniu usług drogą elektroniczną (UŚUDE):
           - Art. 5 - obowiązki informacyjne usługodawcy
           - Art. 8 - obowiązkowe elementy regulaminu
           - Art. 10 - zakaz spamu

        2. Ustawy o prawach konsumenta:
           - Art. 12 - obowiązki informacyjne
           - Art. 27-38 - prawo odstąpienia od umowy
           - Załącznik nr 2 - wzór formularza odstąpienia

        3. Kodeksu cywilnego:
           - Art. 384-385⁴ - wzorce umowne i klauzule abuzywne
           - Art. 556-576 - rękojmia za wady
           - Art. 66¹-66² - oferta elektroniczna

        Tworzysz dokumenty, które:
        - Są zgodne z wszystkimi wymogami prawnymi
        - Chronią interesy firmy w granicach prawa
        - Są zrozumiałe dla przeciętnego użytkownika
        - Nie zawierają klauzul niedozwolonych (abuzywnych)

        UWAGA: Dokument ma charakter wzoru i wymaga weryfikacji przez prawnika.""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    consumer_section = ""
    if not b2b_only:
        consumer_section = f"""
        DLA KONSUMENTÓW (zgodnie z ustawą o prawach konsumenta):

        A) PRAWO ODSTĄPIENIA OD UMOWY (Art. 27):
           - Konsument ma prawo odstąpić od umowy w terminie 14 dni bez podania przyczyny
           - Termin biegnie od dnia zawarcia umowy (usługi) lub otrzymania towaru
           - Wzór formularza odstąpienia zgodny z Załącznikiem nr 2 do ustawy

        B) WYJĄTKI OD PRAWA ODSTĄPIENIA (Art. 38):
           {exceptions_text}

        C) OBOWIĄZKI INFORMACYJNE (Art. 12):
           - Wszystkie wymagane informacje muszą być jasno przedstawione
           - Ceny brutto z VAT
           - Pełne koszty dostawy przed zamówieniem

        D) RĘKOJMIA (Art. 556-576 KC):
           - 2 lata odpowiedzialności za wady
           - Domniemanie istnienia wady przy zgłoszeniu w ciągu roku
        """

    task = Task(
        description=f"""
        Stwórz profesjonalny regulamin świadczenia usług drogą elektroniczną.

        ═══════════════════════════════════════════════════════════════════
        DANE USŁUGODAWCY (Art. 5 UŚUDE):
        ═══════════════════════════════════════════════════════════════════
        Nazwa: {company_name}
        Adres: {company_address}
        NIP: {company_nip or "[DO UZUPEŁNIENIA]"}
        REGON: {company_regon or "[DO UZUPEŁNIENIA]"}
        KRS: {company_krs or "nie dotyczy (działalność gospodarcza)"}
        Email: {contact_email or "[DO UZUPEŁNIENIA]"}
        Telefon: {contact_phone or "[DO UZUPEŁNIENIA]"}
        Strona: {website_url or "[DO UZUPEŁNIENIA]"}

        ═══════════════════════════════════════════════════════════════════
        CHARAKTERYSTYKA USŁUGI:
        ═══════════════════════════════════════════════════════════════════
        Typ usługi: {service_type_pl}
        Opis: {service_description or "[OPIS USŁUGI]"}
        Odbiorcy: {"Wyłącznie przedsiębiorcy (B2B)" if b2b_only else "Konsumenci i przedsiębiorcy (B2C i B2B)"}
        Model subskrypcyjny: {"Tak" if subscription_based else "Nie"}
        Okres próbny: {"Tak - " + str(free_trial_days) + " dni" if free_trial else "Nie"}
        Treści cyfrowe: {"Tak - " + digital_content_description if digital_content else "Nie"}

        ═══════════════════════════════════════════════════════════════════
        PŁATNOŚCI:
        ═══════════════════════════════════════════════════════════════════
        Model cenowy: {pricing_model or "wg cennika na stronie"}
        Warunki płatności: {payment_terms or "przedpłata"}
        Polityka zwrotów: {refund_policy or "zgodnie z ustawą o prawach konsumenta"}

        ═══════════════════════════════════════════════════════════════════
        WYMAGANIA PRAWNE - REGULAMIN MUSI ZAWIERAĆ (Art. 8 UŚUDE):
        ═══════════════════════════════════════════════════════════════════

        § 1. POSTANOWIENIA OGÓLNE I DEFINICJE
        - Definicje wszystkich istotnych pojęć
        - Dane usługodawcy zgodne z Art. 5 UŚUDE
        - Zakres przedmiotowy regulaminu

        § 2. RODZAJE I ZAKRES USŁUG (Art. 8 ust. 3 pkt 1 UŚUDE)
        - Szczegółowy opis wszystkich usług
        - Funkcjonalności dostępne dla użytkowników
        - Różnice między planami/pakietami (jeśli dotyczy)

        § 3. WARUNKI ŚWIADCZENIA USŁUG (Art. 8 ust. 3 pkt 2 UŚUDE)
        - Wymagania techniczne (przeglądarka, system, połączenie)
        - Zakaz dostarczania treści o charakterze bezprawnym
        - Zagrożenia związane z korzystaniem z usług elektronicznych

        § 4. WARUNKI ZAWIERANIA UMÓW (Art. 8 ust. 3 pkt 3 UŚUDE)
        - Proces rejestracji i zawierania umowy
        - Moment zawarcia umowy
        - Potwierdzenie zawarcia umowy

        § 5. WARUNKI ROZWIĄZYWANIA UMÓW (Art. 8 ust. 3 pkt 3 UŚUDE)
        - Wypowiedzenie umowy przez użytkownika
        - Wypowiedzenie umowy przez usługodawcę
        - Skutki rozwiązania umowy

        § 6. PRAWA I OBOWIĄZKI STRON
        - Obowiązki usługodawcy
        - Obowiązki użytkownika
        - Zasady korzystania z usługi

        § 7. PŁATNOŚCI I ROZLICZENIA
        - Cennik i sposób jego aktualizacji
        - Metody płatności
        - Faktury VAT
        {"- Automatyczne odnawianie subskrypcji" if subscription_based else ""}

        § 8. TRYB POSTĘPOWANIA REKLAMACYJNEGO (Art. 8 ust. 3 pkt 4 UŚUDE)
        - Sposób składania reklamacji
        - Termin rozpatrzenia (14 dni)
        - Forma odpowiedzi

        {consumer_section}

        § 9. ODPOWIEDZIALNOŚĆ
        - Zakres odpowiedzialności usługodawcy
        - Ograniczenia odpowiedzialności (zgodne z prawem)
        - Siła wyższa
        - BEZ KLAUZUL ABUZYWNYCH (Art. 385³ KC)

        § 10. WŁASNOŚĆ INTELEKTUALNA
        - Prawa autorskie do usługi
        - Licencja dla użytkownika
        - Zakazy kopiowania/rozpowszechniania

        § 11. OCHRONA DANYCH OSOBOWYCH (RODO)
        - Odniesienie do polityki prywatności
        - Administrator danych
        - Podstawa przetwarzania

        § 12. POSTANOWIENIA KOŃCOWE
        - Procedura zmiany regulaminu
        - Prawo właściwe (prawo polskie)
        - Sąd właściwy (dla przedsiębiorców)
        - Pozasądowe rozwiązywanie sporów (platforma ODR)

        ═══════════════════════════════════════════════════════════════════
        FORMAT ODPOWIEDZI (JSON):
        ═══════════════════════════════════════════════════════════════════

        {{
            "title": "REGULAMIN ŚWIADCZENIA USŁUG DROGĄ ELEKTRONICZNĄ",
            "service_provider": "{company_name}",
            "version": "1.0",
            "effective_date": "{_get_current_date()}",
            "legal_basis": [
                "Ustawa z dnia 18 lipca 2002 r. o świadczeniu usług drogą elektroniczną",
                "Ustawa z dnia 30 maja 2014 r. o prawach konsumenta",
                "Kodeks cywilny"
            ],
            "sections": [
                {{
                    "number": "§ 1",
                    "title": "POSTANOWIENIA OGÓLNE",
                    "content": "treść sekcji z numerowanymi punktami",
                    "legal_reference": "Art. 5 i 8 UŚUDE"
                }}
            ],
            "full_text": "pełna sformatowana treść regulaminu",
            "consumer_rights_summary": "podsumowanie praw konsumenta (jeśli B2C)",
            "withdrawal_form": "wzór formularza odstąpienia (jeśli B2C)",
            "technical_requirements": ["lista wymagań technicznych"],
            "legal_notices": ["wymagane prawnie informacje"],
            "disclaimer": "Niniejszy dokument stanowi wzór i wymaga weryfikacji przez radcę prawnego lub adwokata przed wdrożeniem."
        }}
        """,
        agent=legal_writer,
        expected_output="Regulamin w formacie JSON zgodny z polskim prawem",
    )

    crew = Crew(
        agents=[legal_writer],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    result_text = str(result)

    # Parsowanie JSON
    json_match = re.search(r'\{[\s\S]*\}', result_text)

    parsed_result = None
    if json_match:
        try:
            parsed_result = json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Dodaj wzór formularza odstąpienia dla B2C
    withdrawal_form = None
    if not b2b_only:
        withdrawal_form = WITHDRAWAL_FORM_TEMPLATE.replace(
            "[NAZWA PRZEDSIĘBIORCY]", company_name
        ).replace(
            "[ADRES PRZEDSIĘBIORCY]", company_address
        ).replace(
            "[EMAIL PRZEDSIĘBIORCY]", contact_email or "[EMAIL]"
        )

    return {
        "success": True,
        "terms_of_service": parsed_result or {"full_text": result_text},
        "legal_basis": {
            "uśude": POLISH_ECOMMERCE_LAW["uśude"],
            "ustawa_konsumencka": POLISH_ECOMMERCE_LAW["ustawa_konsumencka"] if not b2b_only else None,
        },
        "withdrawal_form": withdrawal_form,
        "withdrawal_exceptions": applicable_exceptions if not b2b_only else None,
        "required_consumer_info": REQUIRED_CONSUMER_INFO if not b2b_only else None,
        "is_b2c": not b2b_only,
        "disclaimer": "Dokument wymaga weryfikacji przez radcę prawnego lub adwokata przed wdrożeniem.",
    }


# =============================================================================
# GENERATOR POLITYKI ZWROTÓW
# =============================================================================

async def generate_return_policy(
    company_name: str,
    company_address: str,
    contact_email: str = "",
    contact_phone: str = "",

    business_type: str = "ecommerce",
    products_type: str = "",

    # Zwroty konsumenckie
    return_period_days: int = 14,  # Minimum ustawowe
    extended_return_period: bool = False,
    extended_days: int = 30,

    # Warunki zwrotów
    accepts_opened_products: bool = True,
    requires_original_packaging: bool = False,

    # Koszty
    free_returns: bool = False,
    return_shipping_cost: str = "",

    # Wyjątki
    non_returnable_products: list[str] = None,
) -> dict:
    """Generuje politykę zwrotów zgodną z ustawą o prawach konsumenta.

    Oparta o:
    - Art. 27-38 ustawy o prawach konsumenta (prawo odstąpienia)
    - Art. 556-576 Kodeksu cywilnego (rękojmia za wady)

    Args:
        company_name: Nazwa firmy
        company_address: Adres firmy
        contact_email: Email do zwrotów
        contact_phone: Telefon do zwrotów
        business_type: Typ działalności
        products_type: Rodzaj produktów
        return_period_days: Okres na zwrot (min. 14 dni dla konsumentów)
        extended_return_period: Czy oferowany wydłużony okres
        extended_days: Liczba dni wydłużonego okresu
        accepts_opened_products: Czy przyjmowane otwarte produkty
        requires_original_packaging: Czy wymagane oryginalne opakowanie
        free_returns: Czy zwroty są bezpłatne
        return_shipping_cost: Koszt zwrotu jeśli płatny
        non_returnable_products: Lista produktów niepodlegających zwrotowi

    Returns:
        Słownik z polityką zwrotów
    """
    llm = _get_llm()

    # Upewnij się że okres zwrotu nie jest krótszy niż ustawowy
    if return_period_days < 14:
        return_period_days = 14

    actual_return_period = extended_days if extended_return_period else return_period_days

    # Przygotuj listę wyjątków
    exceptions_list = []
    if non_returnable_products:
        for product in non_returnable_products:
            # Dopasuj do ustawowych wyjątków
            for exc in WITHDRAWAL_EXCEPTIONS:
                if any(keyword in product.lower() for keyword in exc["example"].lower().split(", ")):
                    exceptions_list.append(exc)
                    break

    policy_writer = Agent(
        role="Specjalista ds. Polityki Zwrotów",
        goal="Tworzyć polityki zwrotów zgodne z polskim prawem konsumenckim",
        backstory=f"""Jesteś ekspertem od praw konsumenta w Polsce. Znasz:

        1. Ustawę o prawach konsumenta:
           - Art. 27: 14 dni na odstąpienie bez przyczyny
           - Art. 28-30: Bieg terminu odstąpienia
           - Art. 31-33: Skutki odstąpienia (zwrot płatności)
           - Art. 34: Obowiązki konsumenta przy odstąpieniu
           - Art. 38: Wyjątki od prawa odstąpienia

        2. Kodeks cywilny:
           - Art. 556-576: Rękojmia za wady (2 lata)
           - Art. 577-581: Gwarancja (dobrowolna)

        Tworzysz polityki, które:
        - Spełniają minimalne wymogi ustawowe
        - Są zrozumiałe dla konsumentów
        - Zawierają wzór formularza odstąpienia
        - Jasno określają procedurę i terminy""",
        tools=[],
        llm=llm,
        verbose=False,
    )

    exceptions_text = ""
    for exc in WITHDRAWAL_EXCEPTIONS:
        exceptions_text += f"\n- {exc['article']}: {exc['description']}"

    task = Task(
        description=f"""
        Stwórz politykę zwrotów i reklamacji zgodną z prawem polskim.

        ═══════════════════════════════════════════════════════════════════
        DANE SPRZEDAWCY:
        ═══════════════════════════════════════════════════════════════════
        Nazwa: {company_name}
        Adres do zwrotów: {company_address}
        Email: {contact_email or "[DO UZUPEŁNIENIA]"}
        Telefon: {contact_phone or "[DO UZUPEŁNIENIA]"}

        ═══════════════════════════════════════════════════════════════════
        CHARAKTERYSTYKA:
        ═══════════════════════════════════════════════════════════════════
        Typ działalności: {business_type}
        Rodzaj produktów: {products_type or "różne"}

        ═══════════════════════════════════════════════════════════════════
        WARUNKI ZWROTÓW:
        ═══════════════════════════════════════════════════════════════════
        Okres na odstąpienie: {actual_return_period} dni {"(wydłużony ponad ustawowe 14 dni)" if extended_return_period else "(ustawowe minimum)"}
        Przyjmowanie otwartych produktów: {"Tak" if accepts_opened_products else "Nie"}
        Wymagane oryginalne opakowanie: {"Tak" if requires_original_packaging else "Nie"}
        Bezpłatne zwroty: {"Tak" if free_returns else "Nie - koszt: " + (return_shipping_cost or "wg cennika przewoźnika")}

        ═══════════════════════════════════════════════════════════════════
        USTAWOWE WYJĄTKI OD PRAWA ODSTĄPIENIA (Art. 38):
        ═══════════════════════════════════════════════════════════════════
        {exceptions_text}

        ═══════════════════════════════════════════════════════════════════
        STRUKTURA POLITYKI:
        ═══════════════════════════════════════════════════════════════════

        1. PRAWO ODSTĄPIENIA OD UMOWY (Art. 27-30)
           - 14 dni od otrzymania towaru (lub {actual_return_period} dni)
           - Bez podania przyczyny
           - Jak liczyć termin

        2. SPOSÓB ODSTĄPIENIA (Art. 30)
           - Oświadczenie o odstąpieniu (email/formularz/pismo)
           - Wzór formularza (Załącznik nr 2 do ustawy)

        3. ZWROT TOWARU (Art. 34)
           - Termin: 14 dni od złożenia oświadczenia
           - Stan towaru
           - Adres do zwrotów

        4. ZWROT PŁATNOŚCI (Art. 32-33)
           - Termin: 14 dni od otrzymania oświadczenia
           - Ta sama metoda płatności
           - Koszty dostawy (najtańszy sposób)

        5. KOSZTY ZWROTU (Art. 34)
           - Kto ponosi koszty odesłania

        6. WYJĄTKI (Art. 38)
           - Produkty niepodlegające zwrotowi

        7. REKLAMACJE - RĘKOJMIA (Art. 556-576 KC)
           - 2 lata odpowiedzialności
           - Domniemanie wady (1 rok)
           - Uprawnienia: naprawa/wymiana/obniżenie ceny/odstąpienie
           - Termin rozpatrzenia: 14 dni

        8. GWARANCJA (jeśli dotyczy)
           - Oddzielnie od rękojmi

        9. DANE KONTAKTOWE

        ═══════════════════════════════════════════════════════════════════
        FORMAT ODPOWIEDZI (JSON):
        ═══════════════════════════════════════════════════════════════════

        {{
            "title": "POLITYKA ZWROTÓW I REKLAMACJI",
            "effective_date": "{_get_current_date()}",
            "legal_basis": [
                "Art. 27-38 ustawy o prawach konsumenta",
                "Art. 556-576 Kodeksu cywilnego (rękojmia)"
            ],
            "sections": [
                {{
                    "number": "1",
                    "title": "tytuł",
                    "content": "treść z odniesieniami do artykułów"
                }}
            ],
            "full_text": "pełna sformatowana treść polityki",
            "quick_facts": [
                {{"label": "Termin odstąpienia", "value": "{actual_return_period} dni"}},
                {{"label": "Termin zwrotu pieniędzy", "value": "14 dni"}},
                {{"label": "Rękojmia", "value": "24 miesiące"}}
            ],
            "withdrawal_form": "wzór formularza odstąpienia",
            "contact_info": {{
                "email": "{contact_email}",
                "phone": "{contact_phone}",
                "address": "{company_address}"
            }}
        }}
        """,
        agent=policy_writer,
        expected_output="Polityka zwrotów w formacie JSON",
    )

    crew = Crew(
        agents=[policy_writer],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    result_text = str(result)

    json_match = re.search(r'\{[\s\S]*\}', result_text)

    parsed_result = None
    if json_match:
        try:
            parsed_result = json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Wzór formularza odstąpienia
    withdrawal_form = WITHDRAWAL_FORM_TEMPLATE.replace(
        "[NAZWA PRZEDSIĘBIORCY]", company_name
    ).replace(
        "[ADRES PRZEDSIĘBIORCY]", company_address
    ).replace(
        "[EMAIL PRZEDSIĘBIORCY]", contact_email or "[EMAIL]"
    )

    return {
        "success": True,
        "return_policy": parsed_result or {"full_text": result_text},
        "legal_basis": {
            "prawo_odstąpienia": {
                "articles": "Art. 27-38 ustawy o prawach konsumenta",
                "period": f"{actual_return_period} dni",
                "refund_deadline": "14 dni od otrzymania oświadczenia",
            },
            "rękojmia": {
                "articles": "Art. 556-576 Kodeksu cywilnego",
                "period": "24 miesiące od wydania rzeczy",
                "presumption": "12 miesięcy domniemanie istnienia wady",
            },
        },
        "withdrawal_form": withdrawal_form,
        "withdrawal_exceptions": WITHDRAWAL_EXCEPTIONS,
        "disclaimer": "Dokument wymaga weryfikacji przez radcę prawnego lub adwokata przed wdrożeniem.",
    }


# =============================================================================
# GENERATOR ZGÓD MARKETINGOWYCH (RODO + PRAWO TELEKOMUNIKACYJNE)
# =============================================================================

async def generate_marketing_consents(
    company_name: str,
    newsletter: bool = True,
    sms_marketing: bool = False,
    phone_marketing: bool = False,
    profiling: bool = False,
    third_party_marketing: bool = False,
) -> dict:
    """Generuje klauzule zgód marketingowych zgodne z RODO i Prawem telekomunikacyjnym.

    Oparte o:
    - Art. 6 ust. 1 lit. a) RODO - zgoda jako podstawa przetwarzania
    - Art. 7 RODO - warunki wyrażenia zgody
    - Art. 172 Prawa telekomunikacyjnego - zgoda na marketing elektroniczny
    - Art. 10 UŚUDE - zakaz niezamówionej informacji handlowej

    Args:
        company_name: Nazwa administratora danych
        newsletter: Czy generować zgodę na newsletter
        sms_marketing: Czy generować zgodę na SMS marketing
        phone_marketing: Czy generować zgodę na telemarketing
        profiling: Czy generować zgodę na profilowanie
        third_party_marketing: Czy generować zgodę na marketing podmiotów trzecich

    Returns:
        Słownik z klauzulami zgód
    """
    consents = []

    if newsletter:
        consents.append({
            "id": "newsletter",
            "type": "email_marketing",
            "required": False,
            "legal_basis": "Art. 6 ust. 1 lit. a) RODO, Art. 10 UŚUDE",
            "text": f"Wyrażam zgodę na otrzymywanie od {company_name} informacji handlowych "
                   f"drogą elektroniczną (newsletter) na podany adres e-mail, zgodnie z art. 10 "
                   f"ustawy o świadczeniu usług drogą elektroniczną.",
            "withdrawal_info": "Zgodę można wycofać w każdym czasie poprzez kliknięcie w link "
                              "rezygnacji w stopce wiadomości lub kontakt z administratorem.",
        })

    if sms_marketing:
        consents.append({
            "id": "sms_marketing",
            "type": "sms_marketing",
            "required": False,
            "legal_basis": "Art. 172 Prawa telekomunikacyjnego",
            "text": f"Wyrażam zgodę na otrzymywanie od {company_name} informacji handlowych "
                   f"za pomocą wiadomości SMS na podany numer telefonu, zgodnie z art. 172 "
                   f"ustawy Prawo telekomunikacyjne.",
            "withdrawal_info": "Zgodę można wycofać w każdym czasie wysyłając SMS o treści STOP "
                              "lub kontaktując się z administratorem.",
        })

    if phone_marketing:
        consents.append({
            "id": "phone_marketing",
            "type": "telemarketing",
            "required": False,
            "legal_basis": "Art. 172 Prawa telekomunikacyjnego",
            "text": f"Wyrażam zgodę na kontakt telefoniczny ze strony {company_name} "
                   f"w celach marketingowych, zgodnie z art. 172 ustawy Prawo telekomunikacyjne.",
            "withdrawal_info": "Zgodę można wycofać w każdym czasie kontaktując się z administratorem.",
        })

    if profiling:
        consents.append({
            "id": "profiling",
            "type": "profiling",
            "required": False,
            "legal_basis": "Art. 6 ust. 1 lit. a) RODO, Art. 22 RODO",
            "text": f"Wyrażam zgodę na profilowanie moich danych przez {company_name} "
                   f"w celu dostosowania treści marketingowych do moich preferencji, "
                   f"zgodnie z art. 22 RODO.",
            "withdrawal_info": "Zgodę można wycofać w każdym czasie kontaktując się z administratorem. "
                              "Wycofanie zgody nie wpływa na zgodność z prawem przetwarzania przed jej wycofaniem.",
        })

    if third_party_marketing:
        consents.append({
            "id": "third_party",
            "type": "third_party_marketing",
            "required": False,
            "legal_basis": "Art. 6 ust. 1 lit. a) RODO",
            "text": f"Wyrażam zgodę na udostępnienie moich danych osobowych przez {company_name} "
                   f"zaufanym partnerom handlowym w celach marketingowych. Lista partnerów "
                   f"dostępna jest w Polityce Prywatności.",
            "withdrawal_info": "Zgodę można wycofać w każdym czasie kontaktując się z administratorem.",
        })

    return {
        "success": True,
        "consents": consents,
        "legal_requirements": {
            "voluntary": "Zgody marketingowe muszą być dobrowolne (Art. 7 RODO)",
            "specific": "Każda zgoda musi być oddzielna i konkretna",
            "informed": "Użytkownik musi być poinformowany o celu przetwarzania",
            "unambiguous": "Zgoda musi być wyrażona jasnym, potwierdzającym działaniem",
            "withdrawable": "Użytkownik musi mieć możliwość łatwego wycofania zgody",
            "documented": "Administrator musi być w stanie wykazać uzyskanie zgody",
        },
        "implementation_notes": [
            "Checkboxy ze zgodami NIE mogą być domyślnie zaznaczone",
            "Zgoda nie może być warunkiem świadczenia usługi (o ile nie jest niezbędna)",
            "Należy przechowywać datę i treść wyrażonej zgody",
            "Proces wycofania zgody musi być równie prosty jak jej wyrażenie",
        ],
        "disclaimer": "Klauzule wymagają weryfikacji prawnej przed wdrożeniem.",
    }


# =============================================================================
# GENERATOR KLAUZULI INFORMACYJNEJ (Art. 13 RODO)
# =============================================================================

async def generate_data_collection_notice(
    company_name: str,
    company_address: str,
    contact_email: str,
    dpo_email: Optional[str] = None,
    collection_purpose: str = "świadczenie usług",
    data_categories: list[str] = None,
    retention_period: str = "",
    recipients: list[str] = None,
    transfer_outside_eu: bool = False,
    transfer_countries: list[str] = None,
) -> dict:
    """Generuje klauzulę informacyjną zgodną z Art. 13 RODO.

    Wymagana przy zbieraniu danych bezpośrednio od osoby.

    Args:
        company_name: Nazwa administratora
        company_address: Adres administratora
        contact_email: Email kontaktowy
        dpo_email: Email IOD (jeśli powołany)
        collection_purpose: Cel zbierania danych
        data_categories: Kategorie zbieranych danych
        retention_period: Okres przechowywania
        recipients: Odbiorcy danych
        transfer_outside_eu: Czy transfer poza EOG
        transfer_countries: Kraje transferu

    Returns:
        Klauzula informacyjna
    """
    if data_categories is None:
        data_categories = ["imię i nazwisko", "adres e-mail", "numer telefonu"]

    if recipients is None:
        recipients = ["podmioty przetwarzające dane na zlecenie administratora"]

    notice = {
        "title": "KLAUZULA INFORMACYJNA",
        "legal_basis": "Art. 13 Rozporządzenia Parlamentu Europejskiego i Rady (UE) 2016/679 (RODO)",
        "sections": [
            {
                "number": "1",
                "title": "Administrator danych",
                "content": f"Administratorem Pani/Pana danych osobowych jest {company_name} "
                          f"z siedzibą w {company_address}. Kontakt: {contact_email}.",
            },
            {
                "number": "2",
                "title": "Inspektor Ochrony Danych",
                "content": f"Kontakt z IOD: {dpo_email}" if dpo_email
                          else "Administrator nie wyznaczył Inspektora Ochrony Danych.",
            },
            {
                "number": "3",
                "title": "Cel i podstawa przetwarzania",
                "content": f"Pani/Pana dane osobowe przetwarzane będą w celu: {collection_purpose}. "
                          f"Podstawą prawną przetwarzania jest Art. 6 ust. 1 lit. b) RODO "
                          f"(wykonanie umowy) oraz Art. 6 ust. 1 lit. f) RODO (prawnie uzasadniony interes).",
            },
            {
                "number": "4",
                "title": "Kategorie danych",
                "content": f"Przetwarzamy następujące kategorie danych: {', '.join(data_categories)}.",
            },
            {
                "number": "5",
                "title": "Odbiorcy danych",
                "content": f"Odbiorcami danych mogą być: {', '.join(recipients)}.",
            },
            {
                "number": "6",
                "title": "Transfer danych",
                "content": (
                    f"Dane mogą być przekazywane do państw trzecich: {', '.join(transfer_countries or [])}. "
                    f"Transfer odbywa się na podstawie standardowych klauzul umownych zatwierdzonych przez Komisję Europejską."
                ) if transfer_outside_eu else "Dane nie są przekazywane poza Europejski Obszar Gospodarczy.",
            },
            {
                "number": "7",
                "title": "Okres przechowywania",
                "content": retention_period or "Dane przechowywane są przez okres niezbędny do realizacji celu, "
                          "a po jego zakończeniu przez okres wymagany przepisami prawa (np. podatkowego) "
                          "lub do czasu przedawnienia roszczeń.",
            },
            {
                "number": "8",
                "title": "Prawa osoby",
                "content": """Przysługuje Pani/Panu prawo do:
                - dostępu do danych (Art. 15 RODO)
                - sprostowania danych (Art. 16 RODO)
                - usunięcia danych (Art. 17 RODO)
                - ograniczenia przetwarzania (Art. 18 RODO)
                - przenoszenia danych (Art. 20 RODO)
                - sprzeciwu (Art. 21 RODO)
                - wniesienia skargi do Prezesa UODO""",
            },
            {
                "number": "9",
                "title": "Dobrowolność podania danych",
                "content": "Podanie danych jest dobrowolne, jednak niezbędne do zawarcia i realizacji umowy.",
            },
            {
                "number": "10",
                "title": "Zautomatyzowane podejmowanie decyzji",
                "content": "Administrator nie podejmuje decyzji opartych wyłącznie na zautomatyzowanym przetwarzaniu, "
                          "w tym profilowaniu, które wywołują skutki prawne lub istotnie wpływają na osobę.",
            },
        ],
    }

    # Wygeneruj pełny tekst
    full_text = f"KLAUZULA INFORMACYJNA\n(Art. 13 RODO)\n\n"
    for section in notice["sections"]:
        full_text += f"{section['number']}. {section['title']}\n{section['content']}\n\n"

    notice["full_text"] = full_text

    return {
        "success": True,
        "notice": notice,
        "legal_basis": "Art. 13 RODO - obowiązek informacyjny przy zbieraniu danych od osoby",
        "required_elements": [
            "Tożsamość i dane kontaktowe administratora",
            "Dane kontaktowe IOD (jeśli powołany)",
            "Cele przetwarzania i podstawa prawna",
            "Prawnie uzasadnione interesy (jeśli dotyczy)",
            "Odbiorcy danych",
            "Informacja o transferze poza EOG (jeśli dotyczy)",
            "Okres przechowywania",
            "Prawa osoby",
            "Informacja o prawie do skargi do organu nadzorczego",
            "Czy podanie danych jest wymogiem ustawowym/umownym",
            "Informacja o zautomatyzowanym podejmowaniu decyzji",
        ],
        "disclaimer": "Klauzula wymaga dostosowania do konkretnej sytuacji i weryfikacji prawnej.",
    }

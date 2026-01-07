# Plan Rozwoju Agentów AI - Agora

## Wizja Strategiczna

**Cel:** Przekształcenie agentów z "generatorów tekstu" w **autonomicznych asystentów biznesowych**, którzy wykonują zadania end-to-end bez interwencji użytkownika.

**Kluczowa metryka sukcesu:** Czas zaoszczędzony przez użytkownika (nie liczba wygenerowanych tekstów)

---

## Faza 1: Fundamenty (MVP+)

### 1.1 System Narzędzi dla Agentów

Obecnie agenci nie mają żadnych tools - mogą tylko "myśleć". Trzeba dodać:

```
backend/app/services/agents/tools/
├── __init__.py
├── web_search.py      # Tavily API - wyszukiwanie w internecie
├── calculator.py      # Obliczenia finansowe
├── pdf_generator.py   # Generowanie PDF
├── image_generator.py # DALL-E integration
└── validators.py      # Walidacja NIP, IBAN, email
```

**Implementacja:**

| Narzędzie | Technologia | Użycie |
|-----------|-------------|--------|
| **Web Search** | **Tavily API** | Trendy, konkurencja, hashtagi, research |
| Calculator | Python eval (sandboxed) | VAT, marże, cashflow |
| PDF Generator | WeasyPrint / ReportLab | Faktury, raporty |
| Image Generator | OpenAI DALL-E 3 | Grafiki do postów |
| Validators | Lokalne funkcje | NIP, REGON, IBAN |

#### Tavily - Główne Narzędzie Web Search

**Dlaczego Tavily:**
- Zoptymalizowany dla AI/LLM - zwraca czyste, strukturyzowane dane
- Szybki (średnio <1s response time)
- Search + Extract w jednym API call
- Wbudowane filtrowanie i ranking relevance
- Competitive pricing dla SaaS

**Integracja Tavily z CrewAI:**

```python
# backend/app/services/agents/tools/web_search.py
from crewai_tools import TavilySearchTool
from langchain_community.tools.tavily_search import TavilySearchResults

class AgoraTavilyTool:
    """Wrapper dla Tavily z konfiguracją Agora"""

    def __init__(self):
        self.search = TavilySearchResults(
            max_results=5,
            search_depth="advanced",  # lub "basic" dla szybszych query
            include_answer=True,
            include_raw_content=False,
            include_images=True,
        )

    def search_trends(self, query: str, topic: str = "general") -> dict:
        """Wyszukiwanie trendów dla marketingu"""
        return self.search.invoke(f"{query} trends 2025 {topic}")

    def search_competitors(self, company: str, industry: str) -> dict:
        """Analiza konkurencji"""
        return self.search.invoke(f"{company} competitors {industry} analysis")

    def search_hashtags(self, topic: str, platform: str = "instagram") -> dict:
        """Trending hashtagi"""
        return self.search.invoke(f"trending {platform} hashtags {topic} 2025")

    def search_market_data(self, query: str) -> dict:
        """Dane rynkowe dla analiz finansowych"""
        return self.search.invoke(f"{query} market data statistics Poland")
```

**Użycie w agentach:**

```python
# backend/app/services/agents/marketing/instagram.py
from crewai import Agent, Task, Crew
from app.services.agents.tools.web_search import AgoraTavilyTool

tavily_tool = AgoraTavilyTool()

instagram_specialist = Agent(
    role="Instagram Specialist",
    goal="Twórz angażujące posty z aktualnymi trendami",
    tools=[tavily_tool.search],  # Agent ma dostęp do web search
    # ...
)

research_task = Task(
    description="""
    1. Wyszukaj aktualne trendy dla: {topic}
    2. Znajdź trending hashtagi na Instagramie
    3. Sprawdź co robi konkurencja
    4. Na podstawie researchu stwórz post
    """,
    agent=instagram_specialist,
)
```

### 1.2 Feedback Loop

Dodać system oceny outputów:

```python
# backend/app/schemas/feedback.py
class TaskFeedback(BaseModel):
    task_id: str
    rating: int = Field(ge=1, le=5)
    used: bool                    # Czy użytkownik użył outputu
    edited: bool                  # Czy musiał edytować
    edit_percentage: int | None   # Jak dużo zmienił (0-100)
    comments: str | None

# Nowy endpoint
POST /api/v1/tasks/{task_id}/feedback
```

**Korzyści:**
- Dane do fine-tuningu
- Metryki jakości per agent
- Identyfikacja słabych punktów

### 1.3 Kontekst Firmowy (Company Knowledge Base)

Rozszerzyć model Company o:

```python
class CompanyKnowledge(BaseModel):
    products: list[Product]           # Katalog produktów
    services: list[Service]           # Lista usług
    competitors: list[str]            # Konkurenci
    unique_selling_points: list[str]  # USP
    past_campaigns: list[Campaign]    # Historia kampanii
    brand_guidelines: str             # Wytyczne marki
    tone_examples: list[str]          # Przykłady tonu
```

**Efekt:** Agenci znają firmę, nie tylko brief.

### 1.4 PDF Generation

```python
# backend/app/services/agents/tools/pdf_generator.py
from weasyprint import HTML, CSS

class PDFGenerator:
    async def generate_invoice_pdf(self, invoice_data: dict) -> bytes:
        """Generuje profesjonalną fakturę PDF"""
        html = self.render_invoice_template(invoice_data)
        return HTML(string=html).write_pdf()

    async def generate_report_pdf(self, report_data: dict) -> bytes:
        """Generuje raport cashflow PDF"""
        html = self.render_report_template(report_data)
        return HTML(string=html).write_pdf()
```

### 1.5 Image Generation

```python
# backend/app/services/agents/tools/image_generator.py
from openai import OpenAI

class ImageGenerator:
    def __init__(self):
        self.client = OpenAI()

    async def generate_post_image(
        self,
        prompt: str,
        style: str = "modern",
        size: str = "1024x1024"
    ) -> str:
        """Generuje grafikę do posta, zwraca URL"""
        response = await self.client.images.generate(
            model="dall-e-3",
            prompt=f"{prompt}. Style: {style}, professional, social media ready",
            size=size,
            quality="standard",
            n=1,
        )
        return response.data[0].url
```

---

## Faza 2: Integracje Zewnętrzne

### 2.1 Marketing - Social Media

**Instagram/Facebook Integration:**

```
backend/app/services/integrations/
├── social/
│   ├── meta.py         # Meta Graph API (Instagram + Facebook)
│   ├── linkedin.py     # LinkedIn API
│   ├── scheduler.py    # Harmonogram publikacji
│   └── analytics.py    # Pobieranie statystyk
```

| Funkcja | Opis |
|---------|------|
| `connect_account()` | OAuth2 flow do połączenia konta |
| `publish_post()` | Publikacja posta |
| `schedule_post()` | Zaplanowanie publikacji |
| `get_analytics()` | Pobranie statystyk postów |
| `get_audience_insights()` | Dane o odbiorcach |

**Nowy flow Instagram Specialist:**
```
Brief → [Tavily Research] → Generowanie → Review → Podgląd → Approval → Publikacja
```

### 2.2 Marketing - Analytics Integration (z Tavily)

```python
class MarketingResearch:
    def __init__(self):
        self.tavily = AgoraTavilyTool()

    async def get_industry_trends(self, industry: str) -> dict:
        """Pobiera trendy branżowe z internetu"""
        return self.tavily.search_trends(industry)

    async def analyze_competitor_content(self, competitor: str) -> dict:
        """Analizuje content konkurencji"""
        return self.tavily.search_competitors(competitor)

    async def get_viral_content_patterns(self, niche: str) -> dict:
        """Znajduje wzorce viralowego contentu"""
        return self.tavily.search(f"viral {niche} content patterns what works")
```

### 2.3 Finanse - Integracje Księgowe

**Priorytetowe integracje:**

| System | Popularność w PL | API |
|--------|------------------|-----|
| Fakturownia | ★★★★★ | REST API |
| iFirma | ★★★★☆ | REST API |
| wFirma | ★★★☆☆ | REST API |
| InFakt | ★★★☆☆ | REST API |

```
backend/app/services/integrations/
├── accounting/
│   ├── base.py           # Abstract interface
│   ├── fakturownia.py    # Fakturownia API
│   ├── ifirma.py         # iFirma API
│   └── wfirma.py         # wFirma API
```

**Nowy flow Invoice Specialist:**
```
Dane → Generowanie → Walidacja → Podgląd PDF → Approval → Wyślij do systemu księgowego
```

### 2.4 Finanse - Integracje Bankowe

**Open Banking (PSD2):**

| Provider | Opis |
|----------|------|
| Kontomatik | Polski agregator bankowy |
| Nordigen | Europejski Open Banking |
| Salt Edge | Globalny provider |

```python
class BankingIntegration:
    async def connect_bank(self, bank_id: str) -> AuthUrl
    async def get_transactions(self,
        account_id: str,
        from_date: date,
        to_date: date
    ) -> list[Transaction]
    async def categorize_transactions(self, transactions: list) -> CategorizedData
```

**Nowy flow Cashflow Analyst:**
```
Auto-import transakcji → Kategoryzacja AI → Analiza → Rekomendacje → Alerty
```

### 2.5 Cashflow Analyst z Tavily

```python
class CashflowResearchTools:
    def __init__(self):
        self.tavily = AgoraTavilyTool()

    async def get_industry_benchmarks(self, industry: str) -> dict:
        """Porównanie z benchmarkami branżowymi"""
        return self.tavily.search(f"{industry} financial benchmarks Poland SME")

    async def get_economic_outlook(self) -> dict:
        """Prognozy ekonomiczne"""
        return self.tavily.search("Poland economic outlook SME forecast 2025")

    async def get_cost_optimization_tips(self, expense_category: str) -> dict:
        """Wskazówki optymalizacji kosztów"""
        return self.tavily.search(f"reduce {expense_category} costs small business tips")
```

---

## Faza 3: Nowi Agenci

### 3.1 HR Department

```
backend/app/services/agents/hr/
├── __init__.py
├── recruiter.py      # Tworzenie ogłoszeń o pracę
├── interviewer.py    # Przygotowanie pytań rekrutacyjnych
└── onboarding.py     # Materiały onboardingowe
```

**HR Recruiter z Tavily:**
- Research wynagrodzeń rynkowych
- Analiza ogłoszeń konkurencji
- Trendy rekrutacyjne w branży

### 3.2 Sales Department

```
backend/app/services/agents/sales/
├── __init__.py
├── proposal.py       # Generowanie ofert
├── crm_assistant.py  # Asystent CRM
└── lead_scorer.py    # Scoring leadów
```

**Sales Proposal z Tavily:**
- Research klienta przed ofertą
- Analiza branży klienta
- Znajdowanie case studies

### 3.3 Legal Department

```
backend/app/services/agents/legal/
├── __init__.py
├── contract_reviewer.py  # Analiza umów
├── gdpr_assistant.py     # Compliance RODO
└── terms_generator.py    # Regulaminy, polityki
```

### 3.4 Customer Support Department

```
backend/app/services/agents/support/
├── __init__.py
├── ticket_handler.py    # Obsługa zgłoszeń
├── faq_generator.py     # Tworzenie FAQ
└── sentiment_analyst.py # Analiza sentymentu
```

---

## Faza 4: Zaawansowane Możliwości

### 4.1 Multi-Agent Collaboration

Agenci współpracujący nad złożonymi zadaniami:

```python
class MarketingCampaignCrew:
    agents = [
        "Market Researcher",      # Tavily research
        "Copywriter",             # Teksty
        "Instagram Specialist",   # Social media
        "Email Marketer",         # Email sequence
        "Analytics Expert"        # Pomiar wyników
    ]

    process = "hierarchical"  # Manager koordynuje
```

### 4.2 Proactive Agents

Agenci działający bez promptu użytkownika:

| Agent | Trigger | Akcja |
|-------|---------|-------|
| Cashflow Monitor | Niski stan konta | Alert + rekomendacje |
| Invoice Reminder | Niezapłacona faktura | Przypomnienie do klienta |
| Content Calendar | Brak zaplanowanych postów | Sugestie contentu |
| Trend Monitor | Nowy trend w branży (Tavily) | Alert + propozycja reakcji |
| Review Monitor | Nowa opinia Google | Analiza + sugerowana odpowiedź |

### 4.3 Voice Interface

```
backend/app/services/voice/
├── speech_to_text.py   # Whisper API
├── text_to_speech.py   # ElevenLabs
└── voice_agent.py      # Konwersacyjny agent
```

### 4.4 Mobile App + Notifications

- Push notifications o statusie zadań
- Quick actions (approve/reject z powiadomienia)
- Widget z podsumowaniem dnia

---

## Faza 5: AI Advancement

### 5.1 Fine-tuned Models

| Model | Trening na | Cel |
|-------|------------|-----|
| Agora-Copy-PL | Polskie teksty marketingowe | Lepszy copywriting |
| Agora-Finance-PL | Polskie dokumenty finansowe | Dokładniejsze faktury |
| Agora-Legal-PL | Polskie umowy | Analiza kontraktów |

### 5.2 RAG Enhancement

```python
class EnhancedMemory:
    # Obecne
    qdrant: VectorStore      # Pamięć semantyczna

    # Nowe
    graph_db: Neo4j          # Relacje między encjami
    time_series: InfluxDB    # Dane czasowe (analytics)
    tavily: TavilySearch     # Real-time web knowledge

    async def get_context(self, query: str) -> Context:
        semantic = await self.qdrant.search(query)
        relations = await self.graph_db.get_related(semantic)
        history = await self.time_series.get_trends(query)
        web_context = await self.tavily.search(query)  # Fresh data
        return Context(semantic, relations, history, web_context)
```

### 5.3 Autonomous Goal Achievement

Agent dostaje cel, sam planuje i wykonuje:

```python
# Input
goal = "Zwiększ engagement na Instagramie o 20% w ciągu miesiąca"

# Agent autonomicznie:
# 1. [Tavily] Analizuje trendy i best practices
# 2. [Tavily] Bada konkurencję
# 3. Tworzy strategię contentową
# 4. Generuje i publikuje posty
# 5. Monitoruje wyniki
# 6. [Tavily] Szuka nowych trendów
# 7. Dostosowuje strategię
# 8. Raportuje postępy
```

---

## Konfiguracja Tavily

### Zmienne środowiskowe

```env
# .env
TAVILY_API_KEY=tvly-xxxxxxxxxxxxx
TAVILY_SEARCH_DEPTH=advanced  # basic | advanced
TAVILY_MAX_RESULTS=5
```

### Config

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...

    # Tavily
    tavily_api_key: str = Field(..., env="TAVILY_API_KEY")
    tavily_search_depth: str = Field("advanced", env="TAVILY_SEARCH_DEPTH")
    tavily_max_results: int = Field(5, env="TAVILY_MAX_RESULTS")
```

### Pricing Tavily (orientacyjnie)

| Plan | Requests/month | Cena |
|------|----------------|------|
| Free | 1,000 | $0 |
| Basic | 10,000 | $30/mo |
| Pro | 100,000 | $200/mo |
| Enterprise | Unlimited | Custom |

**Rekomendacja:** Start z Basic, przejście na Pro przy >50 aktywnych firmach.

---

## Roadmap Wizualny

```
Q1 2025                    Q2 2025                    Q3 2025                    Q4 2025
┌─────────────────────────┬─────────────────────────┬─────────────────────────┬─────────────────────────┐
│      FAZA 1             │      FAZA 2             │      FAZA 3             │      FAZA 4             │
│                         │                         │                         │                         │
│ ☐ Tavily Integration    │ ☐ Social Media API      │ ☐ HR Department         │ ☐ Multi-Agent Crews     │
│ ☐ Feedback loop         │ ☐ Integracje księgowe   │ ☐ Sales Department      │ ☐ Proactive Agents      │
│ ☐ Company Knowledge     │ ☐ Open Banking          │ ☐ Legal Department      │ ☐ Voice Interface       │
│ ☐ PDF Generation        │ ☐ Analytics Dashboard   │ ☐ Support Department    │ ☐ Mobile App            │
│ ☐ Image Generation      │ ☐ Scheduler             │ ☐ Agent Marketplace     │ ☐ Autonomous Goals      │
│                         │                         │                         │                         │
└─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

---

## Priorytety per Agent (Quick Wins)

### Instagram Specialist - Top 3 usprawnienia:
1. **Tavily Hashtag Research** - trending hashtagi z real-time search
2. **Image Generation (DALL-E)** - pełny post, nie tylko tekst
3. **Meta Business Suite Integration** - publikacja i analytics

### Copywriter - Top 3 usprawnienia:
1. **Tavily SEO Research** - keyword research przed pisaniem
2. **Company Products KB** - zna produkty firmy
3. **A/B Testing Framework** - porównywanie wariantów

### Invoice Specialist - Top 3 usprawnienia:
1. **Fakturownia Integration** - wystawianie prawdziwych faktur
2. **Contractor Database** - autouzupełnianie danych
3. **PDF Generation** - profesjonalny dokument

### Cashflow Analyst - Top 3 usprawnienia:
1. **Bank Integration** - auto-import transakcji
2. **Tavily Market Research** - benchmarki branżowe, prognozy
3. **Alert System** - powiadomienia o anomaliach

---

## KPIs do Monitorowania

| Metryka | Cel Faza 1 | Cel Faza 2 | Cel Faza 4 |
|---------|------------|------------|------------|
| Czas na zadanie (user) | -30% | -60% | -90% |
| Output acceptance rate | 60% | 75% | 90% |
| Tasks per user/month | 10 | 30 | 100 |
| End-to-end automation | 0% | 40% | 80% |
| Tavily searches/task | 2-3 | 3-5 | 5-10 |
| Churn rate | <10% | <7% | <5% |
| NPS | 30 | 50 | 70 |

---

## Szacowane Zasoby

| Faza | Zakres | Zespół |
|------|--------|--------|
| Faza 1 | Fundamenty + Tavily | 1 backend + 1 frontend |
| Faza 2 | Integracje | 2 backend + 1 frontend + 1 devops |
| Faza 3 | Nowi agenci | 2 backend + 1 AI/ML + 1 frontend |
| Faza 4 | Zaawansowane | 3 backend + 2 AI/ML + 2 frontend + 1 mobile |

---

## Appendix: Tavily vs Alternatywy

| Cecha | Tavily | SerpAPI | Google Custom Search |
|-------|--------|---------|---------------------|
| AI-optimized output | ✅ | ❌ | ❌ |
| Speed | Fast | Medium | Medium |
| Include answer | ✅ | ❌ | ❌ |
| Pricing | $$ | $$$ | $ |
| Rate limits | Generous | Strict | Very strict |
| CrewAI integration | Native | Manual | Manual |

**Wniosek:** Tavily to najlepszy wybór dla agentów AI - natywna integracja z LangChain/CrewAI i output zoptymalizowany pod LLM.

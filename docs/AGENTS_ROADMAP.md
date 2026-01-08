# Plan Rozwoju Agentów AI - Agora

> **Ostatnia aktualizacja:** Styczeń 2026
> **Status ogólny:** Faza 1 ~100%, Faza 2 ~30%, Faza 3 ~85%, Faza 4 ~50%

## Wizja Strategiczna

**Cel:** Przekształcenie agentów z "generatorów tekstu" w **autonomicznych asystentów biznesowych**, którzy wykonują zadania end-to-end bez interwencji użytkownika.

**Kluczowa metryka sukcesu:** Czas zaoszczędzony przez użytkownika (nie liczba wygenerowanych tekstów)

---

## Faza 1: Fundamenty (MVP+) - ~80% DONE

### 1.1 System Narzędzi dla Agentów

```
backend/app/services/agents/tools/
├── __init__.py
├── web_search.py      ✅ Tavily API - wyszukiwanie w internecie
├── calculator.py      ✅ Obliczenia finansowe (VAT, marże, cashflow)
├── pdf_generator.py   ✅ Generowanie PDF (WeasyPrint)
├── image_generator.py ✅ Together.ai FLUX integration
└── validators.py      ✅ Walidacja NIP, IBAN, REGON, PESEL, email, telefon
```

**Status implementacji:**

| Narzędzie | Technologia | Status | Uwagi |
|-----------|-------------|--------|-------|
| **Web Search** | **Tavily API** | ✅ DONE | TavilySearchTool, TavilyTrendsTool, TavilyCompetitorTool |
| Calculator | Python Decimal | ✅ DONE | VAT, marże, narzut, cashflow, procenty |
| PDF Generator | WeasyPrint | ✅ DONE | Faktury i raporty |
| Image Generator | Together.ai FLUX | ✅ DONE | Zastąpiło DALL-E (tańsze) |
| Validators | Python regex | ✅ DONE | NIP, REGON, IBAN, PESEL, email, telefon |

#### Tavily - ✅ ZAIMPLEMENTOWANE

Pełna integracja z 3 narzędziami:
- `TavilySearchTool` - ogólne wyszukiwanie
- `TavilyTrendsTool` - trendy social media
- `TavilyCompetitorTool` - analiza konkurencji

Lokalizacja: `backend/app/services/agents/tools/web_search.py`

### 1.2 Feedback Loop - ⏳ CZĘŚCIOWO

```python
# ✅ Zaimplementowane: Zapis ratingu w task output
# ❌ Brakuje: Endpoint /api/v1/tasks/{task_id}/feedback
# ❌ Brakuje: Wykorzystanie feedbacku do fine-tuningu
```

### 1.3 Kontekst Firmowy (Company Knowledge Base) - ✅ DONE

Pełna implementacja z ~70 polami w modelu `CompanyKnowledge`:

```python
# backend/app/models/company.py
class CompanyKnowledge(BaseModel):
    brand_identity: BrandIdentity       # ✅ osobowość, wartości, USP
    target_audience: TargetAudience     # ✅ demografia, bolączki, cele
    communication_style: CommunicationStyle  # ✅ ton, emoji, słowa
    content_preferences: ContentPreferences  # ✅ hashtagi, formaty
    products: list[Product]             # ✅ produkty z cenami
    services: list[Service]             # ✅ usługi
    competitors: list[Competitor]       # ✅ konkurencja
```

**NOWE:** Brand Context Builder (`backend/app/services/agents/brand_context.py`)
- Konwertuje CompanyKnowledge na strukturyzowany prompt
- Agent-specific contexts (Instagram vs Copywriter vs Campaign)

### 1.4 PDF Generation - ✅ DONE

Lokalizacja: `backend/app/services/agents/tools/pdf_generator.py`

Funkcje:
- `generate_invoice_pdf()` - profesjonalne faktury
- `generate_report_pdf()` - raporty finansowe
- Templates z logo firmy i stylowaniem

### 1.5 Image Generation - ✅ DONE (zmieniona technologia)

Lokalizacja: `backend/app/services/agents/tools/image_generator.py`

**Zmiana:** Zamiast DALL-E używamy **Together.ai FLUX**:
- `black-forest-labs/FLUX.1-schnell` - szybkie generowanie
- Tańsze niż DALL-E
- Obsługa różnych platform (Instagram, Facebook, LinkedIn)

---

## Faza 2: Integracje Zewnętrzne - ~30% DONE

### 2.1 Marketing - Social Media

```
backend/app/services/integrations/
├── social/
│   ├── meta.py         ✅ Meta Graph API (Instagram + Facebook)
│   ├── linkedin.py     ❌ DO ZROBIENIA
│   ├── scheduler.py    ✅ Harmonogram publikacji (w meta.py)
│   └── analytics.py    ⏳ CZĘŚCIOWO (basic insights)
```

**Meta Integration - ✅ ZAIMPLEMENTOWANE:**

Lokalizacja: `backend/app/services/integrations/meta.py`

| Funkcja | Status |
|---------|--------|
| `connect_account()` - OAuth2 | ✅ |
| `publish_post()` - Publikacja | ✅ |
| `schedule_post()` - Planowanie | ✅ |
| `get_media_insights()` - Statystyki | ✅ |
| `get_account_insights()` - Konto | ✅ |

### 2.2 Finanse - Integracje Księgowe - ❌ TODO

**Priorytetowe integracje do zrobienia:**

| System | Popularność w PL | Status |
|--------|------------------|--------|
| Fakturownia | ★★★★★ | ❌ TODO |
| iFirma | ★★★★☆ | ❌ TODO |
| wFirma | ★★★☆☆ | ❌ TODO |

### 2.3 Finanse - Integracje Bankowe - ❌ TODO

Open Banking (PSD2) - do zrobienia w przyszłości.

---

## Faza 3: Nowi Agenci - ~85% DONE

### 3.1 HR Department - ✅ DONE

```
backend/app/services/agents/hr/
├── __init__.py         ✅
├── recruiter.py        ✅ Tworzenie ogłoszeń o pracę
├── interviewer.py      ✅ Przygotowanie pytań rekrutacyjnych
└── onboarding.py       ✅ Materiały onboardingowe
```

### 3.2 Sales Department - ✅ DONE

```
backend/app/services/agents/sales/
├── __init__.py         ✅
├── proposal.py         ✅ Generowanie ofert
└── lead_scorer.py      ✅ Scoring leadów
```

### 3.3 Legal Department - ✅ DONE

```
backend/app/services/agents/legal/
├── __init__.py         ✅
├── contract_reviewer.py  ✅ Analiza umów
├── gdpr_assistant.py     ✅ Compliance RODO
└── terms_generator.py    ✅ Regulaminy, polityki
```

### 3.4 Customer Support Department - ✅ DONE

```
backend/app/services/agents/support/
├── __init__.py         ✅
├── ticket_handler.py   ✅ Obsługa zgłoszeń
├── faq_generator.py    ✅ Tworzenie FAQ
└── sentiment_analyst.py ✅ Analiza sentymentu
```

---

## Faza 4: Zaawansowane Możliwości - ~50% DONE

### 4.1 Multi-Agent Collaboration - ✅ DONE

Lokalizacja: `backend/app/services/agents/campaigns.py`

Zaimplementowane kampanie:
- `SOCIAL_MEDIA` - Instagram + Image Generator
- `FULL_MARKETING` - Copywriter + Instagram + Image
- `PRODUCT_LAUNCH` - Pełny pakiet dla nowego produktu
- `PROMO_CAMPAIGN` - Materiały promocyjne

### 4.2 Proactive Agents - ⏳ CZĘŚCIOWO

```
backend/app/services/agents/monitoring/
├── __init__.py         ✅
├── alerts.py           ✅ System alertów
├── trends.py           ✅ Monitoring trendów (Tavily)
└── scheduler.py        ✅ Harmonogram zadań
```

**Do zrobienia:**
- ❌ Auto-triggering przy niskim stanie konta
- ❌ Auto-generowanie content calendar

### 4.3 Voice Interface - ✅ DONE

```
backend/app/services/voice/
├── __init__.py         ✅
├── speech_to_text.py   ✅ OpenAI Whisper
├── text_to_speech.py   ✅ OpenAI TTS
└── voice_agent.py      ✅ Konwersacyjny agent
```

### 4.4 Autonomous Goals - ⏳ CZĘŚCIOWO

```
backend/app/services/agents/goals/
├── __init__.py         ✅
├── planner.py          ✅ Planowanie celów
├── executor.py         ✅ Wykonywanie kroków
└── tracker.py          ✅ Śledzenie postępów
```

### 4.5 Mobile App + Notifications - ❌ TODO

Nie rozpoczęte.

---

## Faza 5: AI Advancement - ~10% DONE

### 5.1 Fine-tuned Models - ❌ TODO

Nie rozpoczęte.

### 5.2 RAG Enhancement - ⏳ CZĘŚCIOWO

```python
# ✅ Zaimplementowane:
qdrant: VectorStore      # Pamięć semantyczna (memory_service)
tavily: TavilySearch     # Real-time web knowledge

# ❌ Do zrobienia:
graph_db: Neo4j          # Relacje między encjami
time_series: InfluxDB    # Dane czasowe
```

Lokalizacja: `backend/app/services/agents/memory.py`

### 5.3 Autonomous Goal Achievement - ⏳ CZĘŚCIOWO

Podstawowa struktura istnieje w `goals/`, ale brak pełnej autonomii.

---

## Roadmap Wizualny - ZAKTUALIZOWANY

```
Q1 2025                    Q2 2025                    Q3 2025                    Q4 2025
┌─────────────────────────┬─────────────────────────┬─────────────────────────┬─────────────────────────┐
│      FAZA 1 ✅          │      FAZA 2             │      FAZA 3             │      FAZA 4             │
│                         │                         │                         │                         │
│ ✅ Tavily Integration   │ ✅ Social Media API     │ ✅ HR Department        │ ✅ Multi-Agent Crews    │
│ ⏳ Feedback loop        │ ❌ Integracje księgowe  │ ✅ Sales Department     │ ⏳ Proactive Agents     │
│ ✅ Company Knowledge    │ ❌ Open Banking         │ ✅ Legal Department     │ ✅ Voice Interface      │
│ ✅ PDF Generation       │ ⏳ Analytics Dashboard  │ ✅ Support Department   │ ❌ Mobile App           │
│ ✅ Image Generation     │ ✅ Scheduler            │ ❌ Agent Marketplace    │ ⏳ Autonomous Goals     │
│ ✅ Calculator           │ ❌ LinkedIn API         │                         │                         │
│ ✅ Validators           │                         │                         │                         │
│                         │                         │                         │                         │
└─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┘

Legenda: ✅ Zrobione | ⏳ Częściowo | ❌ Do zrobienia
```

---

## Priorytety DO ZROBIENIA (Quick Wins)

### ~~Najwyższy priorytet (Faza 1 - dokończenie):~~ ✅ UKOŃCZONE

1. ~~**Calculator Tool** - obliczenia finansowe (VAT, marże, cashflow)~~ ✅
2. ~~**Validators Tool** - walidacja NIP, IBAN, REGON~~ ✅

### Najwyższy priorytet (Faza 2):

1. **Fakturownia Integration** - wystawianie prawdziwych faktur
2. **LinkedIn API** - publikacja na LinkedIn

### Średni priorytet:

3. **Feedback Endpoint** - `/api/v1/tasks/{task_id}/feedback`
4. **Open Banking** - import transakcji bankowych

### Niższy priorytet:

5. **Mobile App** - push notifications
6. **Agent Marketplace** - publiczny katalog agentów

---

## Dodatkowe narzędzia ZAIMPLEMENTOWANE (nie w oryginalnym roadmap)

| Narzędzie | Lokalizacja | Opis |
|-----------|-------------|------|
| Google Calendar | `integrations/google_calendar.py` | Integracja kalendarza |
| Brand Context Builder | `agents/brand_context.py` | Rich context dla agentów |
| Memory Service | `agents/memory.py` | Pamięć agentów z Qdrant |

---

## KPIs do Monitorowania

| Metryka | Cel Faza 1 | Aktualny Status |
|---------|------------|-----------------|
| Tools implemented | 5/5 | 5/5 (100%) ✅ |
| Departments | 4/4 | 4/4 (100%) ✅ |
| Integrations | 4 | 2 (50%) |
| Voice Interface | Yes | Yes (100%) ✅ |
| Multi-Agent | Yes | Yes (100%) ✅ |

---

## Appendix: Architektura Agentów

```
┌─────────────────────────────────────────────────────────────────┐
│                         DEPARTMENTS                              │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────┤
│ Marketing│ Finance  │    HR    │  Sales   │  Legal   │ Support │
├──────────┼──────────┼──────────┼──────────┼──────────┼─────────┤
│Instagram │Invoice   │Recruiter │Proposal  │Contract  │Ticket   │
│Copywriter│Cashflow  │Interview │LeadScore │GDPR      │FAQ      │
│          │          │Onboard   │          │Terms     │Sentiment│
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬────┘
     │          │          │          │          │          │
     └──────────┴──────────┴──────────┴──────────┴──────────┘
                              │
                    ┌─────────┴─────────┐
                    │   TOOLS ✅ 100%   │
                    ├───────────────────┤
                    │ ✅ Tavily Search  │
                    │ ✅ PDF Generator  │
                    │ ✅ Image Generator│
                    │ ✅ Calculator     │
                    │ ✅ Validators     │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │   INTEGRATIONS    │
                    ├───────────────────┤
                    │ ✅ Meta API       │
                    │ ✅ Google Calendar│
                    │ ❌ LinkedIn       │
                    │ ❌ Fakturownia    │
                    │ ❌ Open Banking   │
                    └───────────────────┘
```

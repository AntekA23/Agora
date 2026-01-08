# Roadmapa: Autonomiczny Scheduling Treści

> **Cel:** Przekształcić Agorę w "wirtualnego pracownika" który samodzielnie planuje i publikuje treści
> **Wizja:** Użytkownik raz konfiguruje preferencje → system działa autonomicznie przez tygodnie/miesiące

---

## Stan Obecny vs Cel

### Teraz (Manualne)
```
Użytkownik → Pisze prompt → Generuje treść → Kopiuje → Sam publikuje
           ↓
     Każdy post = osobna akcja
     Żadnej automatyzacji
     Użytkownik musi pamiętać o publikacji
```

### Cel (Autonomiczne)
```
Użytkownik → Konfiguruje raz strategię → System sam:
                                         ├── Generuje treści
                                         ├── Planuje optymalny czas
                                         ├── Czeka na approval (opcjonalne)
                                         └── Publikuje automatycznie

     Tygodnie pracy = 1 konfiguracja
     "Pracownik" który nie śpi
```

---

## FAZA 1: Content Queue (Fundament)

### Cel Fazy
Umożliwić użytkownikowi zapisywanie wygenerowanych treści do kolejki zamiast natychmiastowego kopiowania.

### 1.1 Model Danych - ScheduledContent

**Plik:** `backend/app/models/scheduled_content.py`

```python
class ScheduledContent(Document):
    """Treść zaplanowana do publikacji."""

    # Identyfikacja
    company_id: str
    created_by: str  # user_id

    # Treść
    content_type: str  # "instagram_post", "facebook_post", "linkedin_post", "email"
    title: str  # Tytuł roboczy dla użytkownika
    content: dict  # Zawartość (tekst, hashtagi, etc.)
    media_urls: list[str]  # URL-e do obrazów/wideo

    # Status
    status: str  # "draft", "queued", "scheduled", "published", "failed"

    # Scheduling
    scheduled_for: datetime | None  # Kiedy opublikować
    published_at: datetime | None  # Kiedy faktycznie opublikowano

    # Źródło
    source_task_id: str | None  # ID zadania które wygenerowało treść
    source_conversation_id: str | None  # ID konwersacji

    # Metadane
    platform_post_id: str | None  # ID posta po publikacji
    engagement_stats: dict | None  # Lajki, komentarze (do późniejszej analizy)

    # Timestamps
    created_at: datetime
    updated_at: datetime
```

### 1.2 API Endpoints

**Plik:** `backend/app/api/v1/endpoints/scheduled_content.py`

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/scheduled-content` | GET | Lista treści użytkownika (filtry: status, type, date range) |
| `/scheduled-content` | POST | Dodaj treść do kolejki |
| `/scheduled-content/{id}` | GET | Szczegóły treści |
| `/scheduled-content/{id}` | PATCH | Aktualizuj (edycja, zmiana czasu) |
| `/scheduled-content/{id}` | DELETE | Usuń z kolejki |
| `/scheduled-content/{id}/publish` | POST | Opublikuj natychmiast |
| `/scheduled-content/queue` | GET | Pełna kolejka z timeline view |

### 1.3 Frontend - Przycisk "Dodaj do kolejki"

**Modyfikacja:** Wyniki zadań (task results)

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Post Instagram gotowy!                                   │
│                                                              │
│  [Treść posta...]                                           │
│                                                              │
│  Co dalej?                                                   │
│  [📋 Kopiuj] [💾 Pobierz] [📅 Dodaj do kolejki] ← NOWY      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Po kliknięciu "Dodaj do kolejki":**
```
┌─────────────────────────────────────────────────────────────┐
│  📅 Zaplanuj publikację                                      │
│                                                              │
│  Tytuł roboczy:                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Post o promocji wiosennej                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Kiedy opublikować?                                          │
│  ○ Dodaj do kolejki (opublikuję później)                    │
│  ○ Zaplanuj na konkretny czas: [____/__/__] [__:__]         │
│  ○ Pozwól AI wybrać optymalny czas                          │
│                                                              │
│  [Anuluj] [Dodaj do kolejki]                                │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Frontend - Widok Kolejki

**Nowa strona:** `frontend/src/app/(dashboard)/queue/page.tsx`

```
┌──────────────────────────────────────────────────────────────┐
│  📅 Kolejka treści                           [+ Nowa treść]  │
│                                                              │
│  Filtry: [Wszystkie ▾] [Wszystkie typy ▾] [Ten tydzień ▾]   │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  📌 ZAPLANOWANE (3)                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 📸 Post: Promocja wiosenna          Śr, 15 sty 18:00  │ │
│  │    Instagram • Auto-publish ON                    [⋮] │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 📸 Post: Nowy produkt                Pt, 17 sty 12:00  │ │
│  │    Instagram • Wymaga approval                    [⋮] │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ ✉️ Email: Newsletter styczeń         Pon, 20 sty 09:00 │ │
│  │    Email • Auto-send ON                           [⋮] │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📝 DRAFTY (2)                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 📸 Post: Walentynki                  Brak terminu      │ │
│  │    Instagram                                      [⋮] │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ ✍️ Copy: Reklama produktu             Brak terminu      │ │
│  │    Facebook Ads                                   [⋮] │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ✅ OPUBLIKOWANE (dziś: 1)                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 📸 Post: Poniedziałkowa motywacja    Dziś 08:00 ✓     │ │
│  │    Instagram • 24 lajki, 3 komentarze             [⋮] │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 1.5 Pliki do Utworzenia (Faza 1)

| Plik | Typ | Opis |
|------|-----|------|
| `backend/app/models/scheduled_content.py` | NOWY | Model ScheduledContent |
| `backend/app/schemas/scheduled_content.py` | NOWY | Pydantic schemas |
| `backend/app/api/v1/endpoints/scheduled_content.py` | NOWY | API endpoints |
| `frontend/src/hooks/use-scheduled-content.ts` | NOWY | React Query hooks |
| `frontend/src/app/(dashboard)/queue/page.tsx` | NOWY | Strona kolejki |
| `frontend/src/components/queue/queue-list.tsx` | NOWY | Lista treści |
| `frontend/src/components/queue/queue-item.tsx` | NOWY | Pojedynczy element |
| `frontend/src/components/queue/schedule-dialog.tsx` | NOWY | Dialog planowania |
| `frontend/src/components/layout/sidebar.tsx` | EDYCJA | Dodać link do kolejki |

### 1.6 Kryteria Sukcesu Fazy 1

- [ ] Użytkownik może dodać wygenerowaną treść do kolejki
- [ ] Użytkownik widzi wszystkie zaplanowane treści w jednym miejscu
- [ ] Użytkownik może edytować/usuwać treści z kolejki
- [ ] Użytkownik może ręcznie ustawić datę publikacji
- [ ] Treści są poprawnie kategoryzowane (drafty, zaplanowane, opublikowane)

---

## FAZA 2: Smart Scheduling (AI Sugestie)

### Cel Fazy
System sugeruje optymalny czas publikacji na podstawie danych i best practices.

### 2.1 Scheduling Intelligence Service

**Plik:** `backend/app/services/scheduling_intelligence.py`

```python
class SchedulingIntelligence:
    """Serwis sugerujący optymalny czas publikacji."""

    # Domyślne optymalne czasy (per platforma)
    DEFAULT_BEST_TIMES = {
        "instagram": {
            "weekday": ["08:00", "12:00", "18:00", "21:00"],
            "weekend": ["10:00", "14:00", "20:00"],
        },
        "facebook": {
            "weekday": ["09:00", "13:00", "16:00"],
            "weekend": ["12:00", "15:00"],
        },
        "linkedin": {
            "weekday": ["07:30", "12:00", "17:30"],
            "weekend": [],  # LinkedIn słaby w weekendy
        },
    }

    async def suggest_time(
        self,
        company_id: str,
        content_type: str,
        content: dict,
    ) -> ScheduleSuggestion:
        """Sugeruj optymalny czas publikacji."""

        # 1. Pobierz historię publikacji firmy
        history = await self._get_publication_history(company_id)

        # 2. Sprawdź co już zaplanowane (unikaj kolizji)
        scheduled = await self._get_scheduled_content(company_id)

        # 3. Analiza treści (czy to news? promocja? evergreen?)
        content_analysis = await self._analyze_content_urgency(content)

        # 4. Oblicz najlepszy slot
        suggestion = self._calculate_best_slot(
            platform=content_type.split("_")[0],  # "instagram_post" → "instagram"
            history=history,
            scheduled=scheduled,
            urgency=content_analysis.urgency,
        )

        return suggestion

    def _calculate_best_slot(self, ...):
        """Algorytm wyboru slotu."""
        # Logika:
        # 1. Weź domyślne optymalne czasy dla platformy
        # 2. Dostosuj na podstawie historycznych wyników firmy
        # 3. Unikaj slotów gdzie już coś zaplanowane
        # 4. Dla pilnych treści - najbliższy dobry slot
        # 5. Dla evergreen - rozłóż równomiernie
```

### 2.2 API dla Sugestii

**Endpoint:** `POST /scheduled-content/suggest-time`

```python
# Request
{
    "content_type": "instagram_post",
    "content": {...},
    "preferences": {
        "earliest": "2025-01-15",
        "latest": "2025-01-20",
        "avoid_weekends": false
    }
}

# Response
{
    "suggested_time": "2025-01-16T18:00:00Z",
    "confidence": 0.85,
    "reasoning": "Środa 18:00 to optymalny czas dla Twojej grupy docelowej. Twoje poprzednie posty o tej porze miały średnio 40% więcej zaangażowania.",
    "alternatives": [
        {"time": "2025-01-17T12:00:00Z", "score": 0.78},
        {"time": "2025-01-15T21:00:00Z", "score": 0.72}
    ]
}
```

### 2.3 Frontend - Inteligentny Wybór Czasu

**Modyfikacja dialogu planowania:**

```
┌─────────────────────────────────────────────────────────────┐
│  📅 Zaplanuj publikację                                      │
│                                                              │
│  ✨ AI sugeruje: Środa, 16 sty o 18:00                      │
│  "To optymalny czas dla Twojej grupy docelowej"             │
│                                                              │
│  [Użyj sugestii] [Wybierz inny czas]                        │
│                                                              │
│  ───────────────────────────────────────────────────────────│
│                                                              │
│  Alternatywy:                                                │
│  ○ Czw, 17 sty 12:00 (78% optymalności)                     │
│  ○ Śr, 15 sty 21:00 (72% optymalności)                      │
│  ○ Własny termin: [____/__/__] [__:__]                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Pliki do Utworzenia/Modyfikacji (Faza 2)

| Plik | Typ | Opis |
|------|-----|------|
| `backend/app/services/scheduling_intelligence.py` | NOWY | Logika sugestii |
| `backend/app/schemas/scheduling.py` | NOWY | Schemas dla sugestii |
| `backend/app/api/v1/endpoints/scheduled_content.py` | EDYCJA | Dodać endpoint sugestii |
| `frontend/src/components/queue/schedule-dialog.tsx` | EDYCJA | Pokazać sugestie AI |
| `frontend/src/hooks/use-scheduling-suggestions.ts` | NOWY | Hook dla sugestii |

### 2.5 Kryteria Sukcesu Fazy 2

- [ ] System sugeruje optymalny czas na podstawie platformy
- [ ] Sugestie uwzględniają już zaplanowane treści (brak kolizji)
- [ ] Użytkownik widzi "reasoning" dlaczego ten czas
- [ ] Użytkownik może wybrać alternatywę lub własny czas
- [ ] Sugestie są spersonalizowane (jeśli jest historia)

---

## FAZA 3: Recurring Content (Automatyczne Serie)

### Cel Fazy
Użytkownik definiuje "regułę" → system automatycznie generuje i planuje treści.

### 3.1 Model - ContentScheduleRule

**Plik:** `backend/app/models/schedule_rule.py`

```python
class ContentScheduleRule(Document):
    """Reguła automatycznego generowania treści."""

    company_id: str
    created_by: str

    # Definicja reguły
    name: str  # "Posty motywacyjne w poniedziałki"
    description: str | None

    # Co generować
    content_type: str  # "instagram_post"
    content_template: dict  # Szablon/prompt dla AI
    # Przykład:
    # {
    #     "prompt_template": "Stwórz motywacyjny post na poniedziałek dla firmy {company_name} w branży {industry}",
    #     "style": "inspirujący",
    #     "include_hashtags": true,
    #     "generate_image": true
    # }

    # Kiedy generować (CRON-like)
    schedule: ScheduleConfig
    # {
    #     "frequency": "weekly",  # daily, weekly, monthly
    #     "days_of_week": [0],    # 0=poniedziałek
    #     "time": "08:00",
    #     "timezone": "Europe/Warsaw"
    # }

    # Zachowanie
    auto_approve: bool  # True = publikuj bez pytania
    notify_before_publish: bool  # Powiadom X minut przed
    notification_minutes: int  # np. 60 = godzinę przed

    # Status
    is_active: bool
    last_generated: datetime | None
    next_generation: datetime | None

    # Limity
    max_queue_size: int  # Max treści w kolejce z tej reguły

    created_at: datetime
    updated_at: datetime
```

### 3.2 Scheduler Worker

**Plik:** `backend/app/workers/content_scheduler.py`

```python
async def process_schedule_rules():
    """Worker sprawdzający reguły i generujący treści."""

    # Uruchamiany co godzinę przez arq

    rules = await ContentScheduleRule.find(
        {"is_active": True, "next_generation": {"$lte": datetime.utcnow()}}
    ).to_list()

    for rule in rules:
        try:
            # 1. Sprawdź czy kolejka nie jest pełna
            queue_count = await ScheduledContent.count_documents({
                "company_id": rule.company_id,
                "source_rule_id": rule.id,
                "status": {"$in": ["queued", "scheduled"]}
            })

            if queue_count >= rule.max_queue_size:
                continue

            # 2. Wygeneruj treść używając odpowiedniego agenta
            content = await generate_content_from_rule(rule)

            # 3. Dodaj do kolejki
            scheduled = ScheduledContent(
                company_id=rule.company_id,
                content_type=rule.content_type,
                content=content,
                status="scheduled" if rule.auto_approve else "pending_approval",
                scheduled_for=calculate_next_slot(rule),
                source_rule_id=rule.id,
            )
            await scheduled.save()

            # 4. Zaktualizuj next_generation
            rule.last_generated = datetime.utcnow()
            rule.next_generation = calculate_next_generation(rule)
            await rule.save()

            # 5. Powiadom użytkownika jeśli wymaga approval
            if not rule.auto_approve:
                await notify_pending_approval(rule, scheduled)

        except Exception as e:
            await log_rule_error(rule, e)
```

### 3.3 API Endpoints dla Reguł

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/schedule-rules` | GET | Lista reguł użytkownika |
| `/schedule-rules` | POST | Utwórz nową regułę |
| `/schedule-rules/{id}` | GET | Szczegóły reguły |
| `/schedule-rules/{id}` | PATCH | Aktualizuj regułę |
| `/schedule-rules/{id}` | DELETE | Usuń regułę |
| `/schedule-rules/{id}/toggle` | POST | Włącz/wyłącz regułę |
| `/schedule-rules/{id}/generate-now` | POST | Wymuś generację teraz |

### 3.4 Frontend - Kreator Reguł

**Nowa strona:** `frontend/src/app/(dashboard)/automation/page.tsx`

```
┌──────────────────────────────────────────────────────────────┐
│  🤖 Automatyzacje                          [+ Nowa reguła]   │
│                                                              │
│  Aktywne reguły automatycznie generują i publikują treści.  │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 🟢 Motywacyjne poniedziałki                           │ │
│  │    Instagram • Co poniedziałek o 08:00                │ │
│  │    Auto-publish: ON • W kolejce: 2/4                  │ │
│  │    Następna generacja: za 3 dni                       │ │
│  │                                    [Edytuj] [⏸️ Pauza] │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 🟢 Piątkowe podsumowanie tygodnia                     │ │
│  │    LinkedIn • Co piątek o 17:00                       │ │
│  │    Wymaga approval • W kolejce: 1/2                   │ │
│  │    Następna generacja: za 5 dni                       │ │
│  │                                    [Edytuj] [⏸️ Pauza] │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 🔴 Newsletter miesięczny                    [PAUSED]   │ │
│  │    Email • 1. dzień miesiąca o 10:00                  │ │
│  │                                    [Edytuj] [▶️ Wznów] │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 3.5 Kreator Reguły (Wizard)

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 Nowa automatyzacja                              Krok 1/4│
│                                                              │
│  Co chcesz automatyzować?                                   │
│                                                              │
│  [📸 Posty Instagram]  [📘 Posty Facebook]                  │
│  [💼 Posty LinkedIn]   [✉️ Newslettery]                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🤖 Nowa automatyzacja                              Krok 2/4│
│                                                              │
│  Jaki rodzaj treści?                                        │
│                                                              │
│  [💪 Motywacyjne]  [📰 Branżowe newsy]  [🎓 Edukacyjne]    │
│  [🏷️ Promocyjne]   [🎉 Okolicznościowe] [✨ Custom]        │
│                                                              │
│  Dodatkowe instrukcje (opcjonalne):                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Zawsze wspominaj o darmowej dostawie powyżej 100zł  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🤖 Nowa automatyzacja                              Krok 3/4│
│                                                              │
│  Jak często?                                                 │
│                                                              │
│  ○ Codziennie o [08:00]                                     │
│  ● Co tydzień: [Pon] [  ] [Śr] [  ] [  ] [  ] [  ]         │
│                o [08:00]                                     │
│  ○ Co miesiąc: dnia [1] o [10:00]                          │
│  ○ Custom (CRON): [____________]                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🤖 Nowa automatyzacja                              Krok 4/4│
│                                                              │
│  Jak ma działać publikacja?                                 │
│                                                              │
│  ○ Pełna autonomia                                          │
│    System generuje i publikuje bez pytania                  │
│                                                              │
│  ● Wymaga mojej zgody                                       │
│    Powiadom mnie [1 godzinę] przed publikacją              │
│    Jeśli nie odpowiem: [Opublikuj mimo wszystko ▾]         │
│                                                              │
│  ○ Tylko generuj do kolejki                                 │
│    Sam zdecyduję kiedy opublikować                          │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Nazwa automatyzacji:                                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Motywacyjne poniedziałki                            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  [Anuluj]                              [Utwórz automatyzację]│
└─────────────────────────────────────────────────────────────┘
```

### 3.6 Pliki do Utworzenia (Faza 3)

| Plik | Typ | Opis |
|------|-----|------|
| `backend/app/models/schedule_rule.py` | NOWY | Model reguł |
| `backend/app/schemas/schedule_rule.py` | NOWY | Pydantic schemas |
| `backend/app/api/v1/endpoints/schedule_rules.py` | NOWY | API endpoints |
| `backend/app/workers/content_scheduler.py` | NOWY | Worker generujący treści |
| `backend/app/services/rule_executor.py` | NOWY | Logika wykonywania reguł |
| `frontend/src/app/(dashboard)/automation/page.tsx` | NOWY | Strona automatyzacji |
| `frontend/src/components/automation/rule-list.tsx` | NOWY | Lista reguł |
| `frontend/src/components/automation/rule-wizard.tsx` | NOWY | Kreator reguł |
| `frontend/src/hooks/use-schedule-rules.ts` | NOWY | React Query hooks |

### 3.7 Kryteria Sukcesu Fazy 3

- [ ] Użytkownik może stworzyć regułę w 4 krokach
- [ ] Reguły automatycznie generują treści według harmonogramu
- [ ] Użytkownik wybiera poziom autonomii (pełna / z approval / tylko draft)
- [ ] System powiadamia przed publikacją (jeśli skonfigurowane)
- [ ] Użytkownik może pauzować/wznawiać reguły
- [ ] Max queue size zapobiega nadmiarowi treści

---

## FAZA 4: Batch Generation (Efektywność)

### Cel Fazy
Wygeneruj wiele treści naraz → wypełnij kalendarz na tydzień/miesiąc.

### 4.1 Batch Generation Service

**Plik:** `backend/app/services/batch_generator.py`

```python
class BatchGenerator:
    """Generuje wiele treści naraz."""

    async def generate_batch(
        self,
        company_id: str,
        request: BatchGenerationRequest,
    ) -> BatchGenerationResult:
        """
        Generuj paczkę treści.

        Przykład request:
        {
            "content_type": "instagram_post",
            "count": 7,
            "theme": "Promocja wiosenna",
            "variety": "high",  # low=podobne, high=różnorodne
            "date_range": {
                "start": "2025-01-20",
                "end": "2025-01-26"
            },
            "auto_schedule": true
        }
        """

        # 1. Wygeneruj prompty dla każdego posta
        prompts = await self._generate_varied_prompts(
            theme=request.theme,
            count=request.count,
            variety=request.variety,
            company_context=await self._get_company_context(company_id),
        )

        # 2. Uruchom generację równolegle (lub sekwencyjnie dla oszczędności)
        contents = await self._generate_contents(prompts, request.content_type)

        # 3. Zaplanuj (jeśli auto_schedule)
        if request.auto_schedule:
            scheduled = await self._schedule_batch(
                contents=contents,
                date_range=request.date_range,
                company_id=company_id,
            )
            return BatchGenerationResult(
                generated=contents,
                scheduled=scheduled,
            )

        return BatchGenerationResult(generated=contents)
```

### 4.2 Frontend - Batch Generator

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 Wypełnij kalendarz                                       │
│                                                              │
│  Wygeneruj wiele treści naraz i zaplanuj publikacje.        │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Typ treści:                                                 │
│  [📸 Instagram ▾]                                           │
│                                                              │
│  Ile postów?                                                 │
│  [3] [5] [7] [14] [Własna liczba: __]                       │
│                                                              │
│  Temat/motyw przewodni:                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Promocja wiosenna - nowa kolekcja kremów            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Różnorodność treści:                                        │
│  [Podobne] [Zróżnicowane] [Bardzo różnorodne]               │
│                                                              │
│  Okres publikacji:                                           │
│  Od: [20/01/2025] Do: [26/01/2025]                          │
│                                                              │
│  ☑️ Automatycznie zaplanuj optymalne czasy                  │
│  ☐ Wymaga mojej zgody przed publikacją                      │
│                                                              │
│  [Generuj 7 postów]                                          │
│                                                              │
│  💡 Szacowany czas: ~2 minuty                                │
│  💡 Koszt: ~7 tokenów z Twojego pakietu                     │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Podgląd Wygenerowanej Paczki

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Wygenerowano 7 postów!                                   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Pon 20.01 08:00 │ Post 1: Powitanie wiosny          │    │
│  │                 │ "Wiosna tuż-tuż! 🌸 Nasza..."     │    │
│  │                 │ [Podgląd] [Edytuj] [Usuń]         │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ Wto 21.01 18:00 │ Post 2: Nowość - krem z retinolem│    │
│  │                 │ "Poznajcie nasz najnowszy..."     │    │
│  │                 │ [Podgląd] [Edytuj] [Usuń]         │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ ...                                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  [Zatwierdź wszystkie] [Edytuj wybrane] [Anuluj wszystko]   │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Pliki do Utworzenia (Faza 4)

| Plik | Typ | Opis |
|------|-----|------|
| `backend/app/services/batch_generator.py` | NOWY | Logika batch generation |
| `backend/app/schemas/batch.py` | NOWY | Schemas dla batch |
| `backend/app/api/v1/endpoints/batch.py` | NOWY | API endpoint |
| `frontend/src/app/(dashboard)/queue/batch/page.tsx` | NOWY | Strona batch |
| `frontend/src/components/batch/batch-wizard.tsx` | NOWY | Kreator batch |
| `frontend/src/components/batch/batch-preview.tsx` | NOWY | Podgląd paczki |

### 4.5 Kryteria Sukcesu Fazy 4

- [ ] Użytkownik może wygenerować 3-30 treści naraz
- [ ] System zapewnia różnorodność treści (nie są identyczne)
- [ ] Treści są automatycznie rozplanowane w czasie
- [ ] Użytkownik widzi podgląd przed zatwierdzeniem
- [ ] Możliwość edycji/usunięcia pojedynczych treści z paczki

---

## FAZA 5: Approval Dashboard (Kontrola)

### Cel Fazy
Centralne miejsce do zatwierdzania treści przed publikacją.

### 5.1 Approval Queue

**Modyfikacja:** `frontend/src/app/(dashboard)/queue/page.tsx`

Dodać sekcję "Wymaga zatwierdzenia":

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠️ WYMAGA ZATWIERDZENIA (3)                                 │
│                                                              │
│  Treści czekające na Twoją decyzję przed publikacją.        │
│  [Zatwierdź wszystkie]                                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 📸 Motywacyjny poniedziałek           Pon 20.01 08:00 │ │
│  │    "Nowy tydzień, nowe możliwości! 💪..."              │ │
│  │    Źródło: Reguła "Motywacyjne poniedziałki"          │ │
│  │    ⏰ Publikacja za: 2 godziny                         │ │
│  │                                                        │ │
│  │    [👀 Podgląd] [✏️ Edytuj] [✅ Zatwierdź] [❌ Odrzuć]│ │
│  └────────────────────────────────────────────────────────┘ │
│  ...                                                         │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Quick Approval Actions

- **Swipe right** = Zatwierdź (na mobile)
- **Swipe left** = Odrzuć (na mobile)
- **Keyboard shortcuts**: `A` = Approve, `R` = Reject, `E` = Edit
- **Bulk actions**: Zatwierdź/Odrzuć wszystkie

### 5.3 Notification System

**Kanały powiadomień:**
- In-app notifications (bell icon)
- Email digest (konfigurowalne)
- Push notifications (PWA - przyszłość)

```python
# backend/app/services/notification_service.py

class NotificationService:
    async def notify_pending_approval(
        self,
        user_id: str,
        content: ScheduledContent,
        minutes_until_publish: int,
    ):
        """Powiadom o treści wymagającej zatwierdzenia."""

        # 1. In-app notification
        await self._create_in_app_notification(
            user_id=user_id,
            type="pending_approval",
            title=f"Treść do zatwierdzenia: {content.title}",
            body=f"Publikacja za {minutes_until_publish} minut",
            action_url=f"/queue?id={content.id}",
        )

        # 2. Email (jeśli włączone)
        if user.email_notifications_enabled:
            await self._send_email_notification(...)
```

### 5.4 Pliki do Utworzenia/Modyfikacji (Faza 5)

| Plik | Typ | Opis |
|------|-----|------|
| `backend/app/services/notification_service.py` | NOWY | Serwis powiadomień |
| `backend/app/models/notification.py` | NOWY | Model powiadomień |
| `backend/app/api/v1/endpoints/notifications.py` | NOWY | API powiadomień |
| `frontend/src/components/notifications/notification-bell.tsx` | NOWY | Bell icon |
| `frontend/src/components/notifications/notification-list.tsx` | NOWY | Lista powiadomień |
| `frontend/src/components/queue/approval-section.tsx` | NOWY | Sekcja approval |
| `frontend/src/app/(dashboard)/queue/page.tsx` | EDYCJA | Dodać approval section |

### 5.5 Kryteria Sukcesu Fazy 5

- [ ] Dedykowana sekcja dla treści wymagających approval
- [ ] Quick actions (jeden klik = zatwierdź/odrzuć)
- [ ] Powiadomienia in-app przed publikacją
- [ ] Email notifications (opcjonalne)
- [ ] Bulk approve/reject
- [ ] Fallback action gdy użytkownik nie odpowie

---

## FAZA 6: Auto-Publish (Pełna Autonomia)

### Cel Fazy
System faktycznie publikuje treści na platformach społecznościowych.

### 6.1 Integracje z Platformami

**Priorytet integracji:**
1. Instagram (via Meta Business API)
2. Facebook (via Meta Business API)
3. LinkedIn (via LinkedIn API)
4. Twitter/X (via Twitter API v2)

### 6.2 Publisher Service

**Plik:** `backend/app/services/publishers/base.py`

```python
from abc import ABC, abstractmethod

class BasePublisher(ABC):
    """Bazowa klasa dla publisherów."""

    @abstractmethod
    async def publish(
        self,
        content: ScheduledContent,
        credentials: PlatformCredentials,
    ) -> PublishResult:
        """Opublikuj treść na platformie."""
        pass

    @abstractmethod
    async def validate_credentials(
        self,
        credentials: PlatformCredentials,
    ) -> bool:
        """Sprawdź czy credentials są ważne."""
        pass

    @abstractmethod
    async def get_post_stats(
        self,
        post_id: str,
        credentials: PlatformCredentials,
    ) -> PostStats:
        """Pobierz statystyki posta."""
        pass
```

**Plik:** `backend/app/services/publishers/instagram.py`

```python
class InstagramPublisher(BasePublisher):
    """Publisher dla Instagram (via Meta Business API)."""

    async def publish(
        self,
        content: ScheduledContent,
        credentials: PlatformCredentials,
    ) -> PublishResult:
        """
        Publikuj na Instagram.

        Flow:
        1. Upload media do Facebook (container)
        2. Create media object na Instagram
        3. Publish media
        """
        # Implementation...
```

### 6.3 Publication Worker

**Plik:** `backend/app/workers/publisher.py`

```python
async def publish_scheduled_content():
    """Worker publikujący zaplanowane treści."""

    # Uruchamiany co minutę

    now = datetime.utcnow()
    window_end = now + timedelta(minutes=2)

    # Znajdź treści do publikacji
    contents = await ScheduledContent.find({
        "status": "scheduled",
        "scheduled_for": {"$gte": now, "$lt": window_end},
    }).to_list()

    for content in contents:
        try:
            # 1. Pobierz credentials
            credentials = await get_platform_credentials(
                company_id=content.company_id,
                platform=content.platform,
            )

            # 2. Pobierz odpowiedni publisher
            publisher = get_publisher(content.platform)

            # 3. Opublikuj
            result = await publisher.publish(content, credentials)

            # 4. Zaktualizuj status
            content.status = "published"
            content.published_at = datetime.utcnow()
            content.platform_post_id = result.post_id
            await content.save()

            # 5. Powiadom użytkownika
            await notify_publication_success(content)

        except Exception as e:
            content.status = "failed"
            content.error_message = str(e)
            await content.save()
            await notify_publication_failure(content, e)
```

### 6.4 Platform Connections UI

**Strona:** `frontend/src/app/(dashboard)/settings/integrations/page.tsx`

```
┌──────────────────────────────────────────────────────────────┐
│  🔗 Integracje                                               │
│                                                              │
│  Połącz swoje konta, aby automatycznie publikować treści.   │
│                                                              │
│  ─────────────────────────────────────────────────────────── │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 📸 Instagram                                           │ │
│  │    ✅ Połączono: @mojakosmetyka                        │ │
│  │    Ostatnia publikacja: wczoraj                        │ │
│  │                               [Odłącz] [Sprawdź status]│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 📘 Facebook                                            │ │
│  │    ⚪ Niepołączono                                     │ │
│  │                                              [Połącz →]│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 💼 LinkedIn                                            │ │
│  │    ⚪ Niepołączono                                     │ │
│  │                                              [Połącz →]│ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 6.5 OAuth Flow dla Platform

```
┌─────────────────────────────────────────────────────────────┐
│  📸 Połącz Instagram                                         │
│                                                              │
│  Krok 1: Zaloguj się do Meta Business Suite                 │
│                                                              │
│  Zostaniesz przekierowany do Meta, gdzie:                   │
│  • Wybierzesz konto Instagram do połączenia                 │
│  • Nadasz uprawnienia do publikowania                       │
│                                                              │
│  Uprawnienia które potrzebujemy:                            │
│  ✓ Publikowanie postów i stories                            │
│  ✓ Dostęp do statystyk                                      │
│  ✗ NIE potrzebujemy dostępu do wiadomości                   │
│                                                              │
│  [Połącz z Instagram →]                                      │
│                                                              │
│  🔒 Twoje dane są bezpieczne. Możesz odłączyć w każdej     │
│     chwili.                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 6.6 Pliki do Utworzenia (Faza 6)

| Plik | Typ | Opis |
|------|-----|------|
| `backend/app/services/publishers/base.py` | NOWY | Bazowy publisher |
| `backend/app/services/publishers/instagram.py` | NOWY | Instagram publisher |
| `backend/app/services/publishers/facebook.py` | NOWY | Facebook publisher |
| `backend/app/services/publishers/linkedin.py` | NOWY | LinkedIn publisher |
| `backend/app/models/platform_credentials.py` | NOWY | Model credentials |
| `backend/app/api/v1/endpoints/integrations.py` | NOWY | API integracji |
| `backend/app/workers/publisher.py` | NOWY | Worker publikujący |
| `frontend/src/app/(dashboard)/settings/integrations/page.tsx` | NOWY | Strona integracji |
| `frontend/src/components/integrations/platform-card.tsx` | NOWY | Karta platformy |
| `frontend/src/components/integrations/oauth-dialog.tsx` | NOWY | Dialog OAuth |

### 6.7 Kryteria Sukcesu Fazy 6

- [ ] Użytkownik może połączyć konto Instagram
- [ ] System automatycznie publikuje zatwierdzone treści
- [ ] Użytkownik jest powiadamiany o sukcesie/błędzie publikacji
- [ ] Statystyki postów są pobierane (lajki, komentarze)
- [ ] Możliwość odłączenia konta w każdej chwili
- [ ] Obsługa błędów (expired token, rate limits)

---

## Harmonogram Implementacji

### Sprint 1-2: Faza 1 (Content Queue) - PRIORYTET 1
- Model ScheduledContent
- API CRUD
- UI kolejki
- Przycisk "Dodaj do kolejki" w wynikach

### Sprint 3: Faza 2 (Smart Scheduling) - PRIORYTET 2
- SchedulingIntelligence service
- Sugestie czasów
- UI z sugestiami

### Sprint 4-5: Faza 3 (Recurring Content) - PRIORYTET 3
- Model ContentScheduleRule
- Scheduler worker
- Kreator reguł (wizard)
- UI automatyzacji

### Sprint 6: Faza 4 (Batch Generation)
- BatchGenerator service
- UI batch wizard
- Podgląd paczki

### Sprint 7: Faza 5 (Approval Dashboard)
- Notification service
- Approval section w kolejce
- Email notifications

### Sprint 8-10: Faza 6 (Auto-Publish)
- Publisher services
- OAuth integration
- Platform credentials
- Publication worker

---

## Metryki Sukcesu

| Metryka | Faza 1 | Faza 3 | Faza 6 |
|---------|--------|--------|--------|
| Czas użytkownika/tydzień | -20% | -50% | -80% |
| Treści/tydzień/użytkownik | +30% | +100% | +200% |
| Regularity publikacji | Manual | Semi-auto | Full auto |
| Churn rate | Baseline | -10% | -30% |

---

## Ryzyka i Mitygacje

| Ryzyko | Mitygacja |
|--------|-----------|
| API limity platform | Rate limiting, retry logic, queue management |
| Token expiration | Auto-refresh, user notification |
| Błędna treść opublikowana | Approval flow, preview, undo window |
| Spam detection | Reasonable frequency limits, content variation |
| User trust | Gradual autonomy increase, always allow manual override |

---

## Kluczowe Zasady

1. **Gradual Autonomy** - Użytkownik stopniowo oddaje kontrolę, nie od razu
2. **Always Override** - Zawsze możliwość ręcznej interwencji
3. **Transparent AI** - Wyjaśniaj dlaczego system coś sugeruje
4. **Fail Safe** - Przy wątpliwościach nie publikuj, zapytaj
5. **Easy Undo** - Łatwe cofanie akcji (gdzie możliwe)

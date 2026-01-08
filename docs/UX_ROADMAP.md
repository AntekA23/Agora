# Roadmapa UX: Uproszczenie Interakcji Człowiek ↔ Agent

> **Cel:** Przekształcić aplikację z "zestawu narzędzi" w "inteligentnego asystenta biznesowego"
> **Kluczowa metryka:** Czas zaoszczędzony przez małe firmy
> **Data utworzenia:** Styczeń 2026

---

## Diagnoza Obecnych Problemów

### Problem 1: Zbyt Wiele Wyborów
- 40+ funkcji agentów w 6 departamentach
- Użytkownik musi wiedzieć który agent jest odpowiedni
- Każdy agent ma osobny formularz z innymi polami

### Problem 2: Rozrzucona Konfiguracja
- Onboarding 3-krokowy (podstawowy)
- Brand Wizard 8-krokowy (zaawansowany)
- Ustawienia marki w Settings
- Użytkownik nie wie co gdzie jest

### Problem 3: Aplikacja = Narzędzie, nie Asystent
- Brak proaktywnych sugestii
- Brak inteligentnego routingu
- Użytkownik musi inicjować każdą akcję

### Problem 4: Skomplikowany Workflow
```
Obecny flow:
Użytkownik → Wybierz dział → Wybierz agenta → Wypełnij formularz → Czekaj → Sprawdź wynik

Idealny flow:
Użytkownik → "Potrzebuję posta na Instagram o nowym produkcie" → Gotowe
```

---

## Wizja Docelowa

### Zasada Główna: "Zero Decyzji Technicznych"

Użytkownik NIGDY nie powinien:
- Wybierać agenta ręcznie
- Znać struktury departamentów
- Wypełniać formularzy technicznych
- Konfigurować parametrów

Użytkownik ZAWSZE powinien:
- Opisać co chce osiągnąć (naturalny język)
- Zatwierdzać wyniki
- Dawać feedback

### Model Interakcji: Asystent Konwersacyjny

```
┌─────────────────────────────────────────────────────┐
│                   CHAT INTERFACE                     │
│                                                      │
│  User: "Potrzebuję materiałów na launch nowego      │
│         produktu - suplementu diety"                 │
│                                                      │
│  Agora: "Rozumiem! Przygotuję dla Ciebie:           │
│          ✓ Post na Instagram z grafiką              │
│          ✓ 3 warianty copy reklamowego              │
│          ✓ Hasło promocyjne                         │
│                                                      │
│          Czy masz zdjęcie produktu? (opcjonalne)    │
│          [Tak, wgram] [Nie, wygeneruj]              │
│                                                      │
│  [Generuj materiały]                                │
└─────────────────────────────────────────────────────┘
```

---

## FAZA 1: Unified Command Center (Priorytet Krytyczny)

### 1.1 Nowa Strona Główna: "Command Center"

**Zastępuje:** Dashboard + rozrzucone formularze

**Elementy:**
```
┌──────────────────────────────────────────────────────────────┐
│  🎯 Co chcesz dziś zrobić?                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Opisz czego potrzebujesz...                            │  │
│  │ np. "Post na Instagram o promocji -20%"                │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ─────────────── lub wybierz szybką akcję ───────────────   │
│                                                              │
│  [📸 Post Social Media]  [✍️ Tekst Reklamowy]  [📄 Faktura]  │
│  [📊 Analiza Cashflow]   [🚀 Kampania]         [📋 Więcej]   │
│                                                              │
│  ─────────────────── Ostatnie zadania ───────────────────   │
│                                                              │
│  • Post Instagram "Nowa kolekcja..." - 2h temu ✓            │
│  • Faktura dla ABC Sp. z o.o. - wczoraj ✓                   │
│  • Copy reklamowe "Promocja świąteczna" - 3 dni temu ✓      │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Inteligentny Router (AI Intent Detection)

**Backend:** Nowy endpoint `/api/v1/assistant/interpret`

```python
# Input
{
  "message": "Potrzebuję posta na Instagram o nowym produkcie"
}

# Output
{
  "intent": "social_media_post",
  "suggested_agents": ["instagram_specialist", "image_generator"],
  "missing_info": ["product_name", "key_benefits"],
  "follow_up_questions": [
    "Jak nazywa się produkt?",
    "Jakie są główne korzyści?"
  ],
  "can_auto_execute": false
}
```

**Logika routingu:**
| Słowa kluczowe | Agent(y) |
|----------------|----------|
| post, instagram, social | instagram_specialist |
| reklama, copy, tekst | copywriter |
| faktura, rachunek | invoice_worker |
| kampania, launch | campaign_service (multi-agent) |
| cv, rekrutacja, ogłoszenie | hr_recruiter |
| umowa, regulamin | legal_terms |

### 1.3 Progressive Questioning

**Zamiast formularza → pytania krok po kroku:**

```
Użytkownik: "Chcę post na Instagram"

Agora: "O czym ma być post?"
Użytkownik: "O nowej kolekcji butów"

Agora: "Świetnie! Mam już info o Twojej marce.
        Chcesz dodać zdjęcie produktu?"
        [Tak] [Nie, wygeneruj grafikę]

Użytkownik: [Nie, wygeneruj grafikę]

Agora: "Generuję post + grafikę dla 'Nowa kolekcja butów'..."
       [████████████░░] 80%
```

### 1.4 Pliki do Modyfikacji (Faza 1)

| Plik | Akcja | Opis |
|------|-------|------|
| `frontend/src/app/(dashboard)/page.tsx` | Przepisać | Command Center zamiast Dashboard |
| `frontend/src/components/command-input.tsx` | NOWY | Input z sugestiami |
| `frontend/src/components/quick-actions.tsx` | NOWY | Szybkie akcje |
| `backend/app/api/v1/endpoints/assistant.py` | NOWY | Intent detection |
| `backend/app/services/assistant/router.py` | NOWY | Logika routingu |

---

## FAZA 2: Simplified Onboarding (Priorytet Wysoki)

### 2.1 Uproszczony Onboarding + Brand Wizard jako Opcja

**Problem:** Dwa osobne flow (3 kroki + 8 kroków) - użytkownik nie wie który użyć

**Rozwiązanie:**
- **Onboarding** → uproszczony "Smart Setup" (2-3 kroki + auto-extraction z www)
- **Brand Wizard** → ZACHOWANY jako opcja zaawansowana w Settings
- Jasne rozróżnienie: "Szybki start" vs "Pełna konfiguracja marki"

### 2.2 Smart Setup Flow

```
KROK 1: Podstawy (Obowiązkowe)
┌─────────────────────────────────────────────┐
│  Jak nazywa się Twoja firma?                │
│  ┌───────────────────────────────────────┐  │
│  │ ABC Sp. z o.o.                        │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Czym się zajmujecie? (1-2 zdania)         │
│  ┌───────────────────────────────────────┐  │
│  │ Sprzedajemy ekologiczne kosmetyki...  │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Macie stronę internetową?                  │
│  ┌───────────────────────────────────────┐  │
│  │ www.abc-kosmetyki.pl                  │  │
│  └───────────────────────────────────────┘  │
│  💡 Wyciągniemy automatycznie więcej info  │
│                                             │
│                              [Dalej →]      │
└─────────────────────────────────────────────┘

KROK 2: Auto-uzupełnienie (AI)
┌─────────────────────────────────────────────┐
│  ✨ Przeanalizowaliśmy Waszą stronę!        │
│                                             │
│  Sprawdź czy dobrze zrozumieliśmy:          │
│                                             │
│  Branża: Kosmetyki naturalne ✓              │
│  Ton: Przyjazny, ekologiczny ✓              │
│  Grupa: Kobiety 25-45, dbające o zdrowie ✓  │
│  Produkty: Kremy, sera, olejki [edytuj]     │
│                                             │
│  [Popraw] [Wszystko OK, zakończ setup →]    │
└─────────────────────────────────────────────┘
```

### 2.3 Kontekstowe Dopytywanie

Zamiast 8-krokowego wizarda → system pyta gdy potrzebuje:

```
Użytkownik: "Stwórz post o promocji"

Agora: "Nie mam jeszcze info o Waszych hashtagach.
        Jakich używacie? (lub pomiń - dopasuję sam)"

        ┌─────────────────────────────────────┐
        │ #ABCKosmetyki #NaturalBeauty        │
        └─────────────────────────────────────┘

        [Użyj tych] [Pomiń, dobierz sam]

        ✓ Zapamiętam na przyszłość
```

### 2.4 Pliki do Modyfikacji (Faza 2)

| Plik | Akcja |
|------|-------|
| `frontend/src/app/(auth)/onboarding/page.tsx` | Przepisać na Smart Setup (uproszczony) |
| `frontend/src/components/brand-wizard.tsx` | ZACHOWAĆ - dostępny w Settings |
| `frontend/src/app/(dashboard)/settings/page.tsx` | Dodać jasne CTA do Brand Wizard |
| `backend/app/api/v1/endpoints/onboarding.py` | NOWY - auto-extraction z www |
| `backend/app/services/website_analyzer.py` | NOWY - scraping + AI extraction |

---

## FAZA 3: One-Click Templates (Priorytet Średni)

### 3.1 Szablony Szybkich Akcji

**Zamiast pustych formularzy → gotowe szablony:**

```
📸 Post Social Media
├── 🆕 Nowy produkt/usługa
├── 🏷️ Promocja/Rabat
├── 💡 Porada/Tip
├── 🎉 Wydarzenie/News
├── 📖 Za kulisami
└── ✨ Customowy

✍️ Tekst Reklamowy
├── 🛒 Reklama produktu
├── 📧 Email marketingowy
├── 🎯 Slogan/Hasło
├── 📄 Opis na stronę
└── ✨ Customowy
```

### 3.2 Template Flow

```
Użytkownik klika: [🏷️ Promocja/Rabat]

┌─────────────────────────────────────────────────┐
│  📣 Post promocyjny                              │
│                                                  │
│  Co promujesz?                                   │
│  ┌────────────────────────────────────────────┐ │
│  │ Krem nawilżający                           │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  Jaki rabat?                                     │
│  [10%] [20%] [30%] [Inna wartość: ___]          │
│                                                  │
│  Do kiedy?                                       │
│  ┌────────────────────────────────────────────┐ │
│  │ 31.01.2026                                 │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  [🚀 Generuj post promocyjny]                   │
└─────────────────────────────────────────────────┘
```

### 3.3 Auto-Recall

System pamięta poprzednie użycia:

```
💡 Ostatnio promowałeś "Serum witaminowe" z rabatem 15%.
   [Użyj podobnych ustawień] [Zacznij od nowa]
```

---

## FAZA 4: Proactive Suggestions (Priorytet Średni)

### 4.1 Smart Notifications

```
┌─────────────────────────────────────────────────┐
│  💡 Sugestie dla Ciebie                         │
│                                                  │
│  📅 Ostatni post był 5 dni temu                 │
│     [Stwórz nowy post]                          │
│                                                  │
│  🔥 Trending: #WiosennaOdnowa pasuje do branży  │
│     [Stwórz post z tym trendem]                 │
│                                                  │
│  📊 Twój najlepszy post miał 2x więcej reakcji  │
│     [Zobacz co zadziałało]                      │
└─────────────────────────────────────────────────┘
```

### 4.2 Content Calendar Suggestions

```
┌─────────────────────────────────────────────────┐
│  📆 Ten tydzień                                  │
│                                                  │
│  Pon  Wto  Śro  Czw  Pią  Sob  Nie              │
│  [+]  [+]  ✓    [+]  [+]  -    -                │
│                                                  │
│  Śro: "Nowa kolekcja wiosenna" ✓ zaplanowany    │
│                                                  │
│  💡 Sugeruję dodać post w piątek                │
│     (Twoja grupa jest aktywna 17:00-19:00)      │
│     [Zaplanuj post na piątek]                   │
└─────────────────────────────────────────────────┘
```

---

## FAZA 5: Simplified Results (Priorytet Średni)

### 5.1 Wyniki z Akcjami

**Obecne:** Surowy tekst wyników
**Nowe:** Wyniki + natychmiastowe akcje

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Post Instagram gotowy!                                   │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 🌸 Wiosenna promocja -20%! 🌸                         │  │
│  │                                                        │  │
│  │ Czas odnowić swoją pielęgnację!                       │  │
│  │ Nasze bestsellerowe kremy teraz 20% taniej.          │  │
│  │                                                        │  │
│  │ 💚 Naturalne składniki                                │  │
│  │ 🐰 Cruelty-free                                       │  │
│  │ ♻️ Eko opakowania                                     │  │
│  │                                                        │  │
│  │ Link w bio! ⬆️                                        │  │
│  │                                                        │  │
│  │ #WiosennaPromocja #NaturalBeauty #ABCKosmetyki       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  [Grafika]                                                   │
│  ┌─────────────────────┐                                    │
│  │    [AI Image]       │                                    │
│  └─────────────────────┘                                    │
│                                                              │
│  Co dalej?                                                   │
│  [📋 Kopiuj tekst] [💾 Pobierz grafikę] [📤 Publikuj]      │
│  [✏️ Edytuj] [🔄 Wygeneruj inny wariant]                   │
│                                                              │
│  Zaplanować publikację?                                      │
│  [Teraz] [Dzisiaj 18:00] [Jutro 12:00] [Wybierz datę]       │
└─────────────────────────────────────────────────────────────┘
```

---

## FAZA 6: Conversation Mode (Przyszłość)

### 6.1 Pełny Chat z Agentem

Docelowo: aplikacja działa jak ChatGPT dla biznesu

```
User: Potrzebuję kompletną kampanię na nowy produkt

Agora: Opowiedz mi o produkcie - co to jest?

User: Nowy krem przeciwzmarszczkowy z retinolem

Agora: Świetnie! Przygotuję:
       1. Post na Instagram z grafiką
       2. 3 warianty copy reklamowego
       3. Hasło promocyjne
       4. Email do bazy klientów

       Chcesz dodać coś jeszcze?

User: Dodaj jeszcze opis na stronę

Agora: Oczywiście! Generuję komplet...
       [████████████████████] 100%

       Gotowe! Oto Twoje materiały:
       [Zobacz wszystko] [Pobierz paczkę ZIP]
```

### 6.2 Voice Mode (Future)

Integracja z istniejącym voice service:
- "Hej Agora, stwórz post o promocji"
- Odpowiedzi głosowe + wizualne

---

## Harmonogram Implementacji (Priorytety)

### Sprint 1-2: Command Center (Faza 1) ⭐ PRIORYTET 1
- Nowy dashboard z inputem tekstowym
- Intent detection API
- Szybkie akcje (6 głównych)
- Lista ostatnich zadań

### Sprint 3-4: Templates (Faza 3) ⭐ PRIORYTET 2
- Biblioteka szablonów (post, copy, faktura)
- Template flows z minimalną ilością pól
- Auto-recall poprzednich ustawień

### Sprint 5-6: Results UX (Faza 5) ⭐ PRIORYTET 3
- Wyniki z natychmiastowymi akcjami
- One-click: kopiuj, pobierz, publikuj
- Scheduling/planowanie

### Sprint 7-8: Smart Setup (Faza 2) ⭐ PRIORYTET 4
- Uproszczony onboarding (2-3 kroki)
- Website analyzer (auto-extraction)
- Brand Wizard ZACHOWANY jako opcja zaawansowana

### Przyszłość: Proactive + Conversation (Faza 4, 6)
- Smart notifications
- Content calendar
- Pełny chat mode
- Voice integration

---

## Metryki Sukcesu

| Metryka | Obecna | Cel Faza 1 | Cel Faza 3 |
|---------|--------|------------|------------|
| Czas do pierwszego zadania | ~5 min | ~30 sek | ~10 sek |
| Kliknięcia do wyniku | 8-12 | 3-5 | 1-3 |
| % użytkowników potrzebujących pomocy | ? | -50% | -80% |
| Zadania/użytkownik/tydzień | ? | +50% | +100% |

---

## Kluczowe Zasady Designu

1. **Zero Jargonu** - "Stwórz post" nie "Instagram Specialist Agent"
2. **Progressive Disclosure** - pytaj tylko gdy trzeba
3. **Smart Defaults** - system wie więcej niż pyta
4. **One-Click Actions** - typowe zadania = 1 klik
5. **Visual Feedback** - pokaż co się dzieje
6. **Undo Friendly** - łatwe cofanie i edycja

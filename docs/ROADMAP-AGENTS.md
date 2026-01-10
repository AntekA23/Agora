# Roadmapa: Inteligentni Agenci z Pamięcią i Kontekstem

## Problem

Obecny system ma krytyczny błąd - **traci kontekst konwersacji**:

```
User: "Stwórz post o Dario - aplikacji dla terapeutów..."
Bot: "Doprecyzuj styl/ton?"
User: "casualowy"
Bot: "Nie jestem pewien czego potrzebujesz" ← UTRATA KONTEKSTU!
```

### Diagnoza problemu

1. **Brak przekazywania kontekstu do `interpret()`** - funkcja analizuje tylko bieżącą wiadomość "casualowy" bez wiedzy o poprzednich
2. **Brak scalania parametrów** - extracted_params z poprzednich wiadomości nie są mergowane
3. **Stateless processing** - każda wiadomość traktowana jak nowa konwersacja
4. **Brak "pamięci roboczej"** - agent nie pamięta co robił przed chwilą

---

## Faza 1: Naprawa Kontekstu Konwersacji (PILNE)

### 1.1 Przekazywanie kontekstu do interpret()

**Plik:** `backend/app/services/assistant/router.py`

```python
async def interpret(
    self,
    message: str,
    conversation_context: dict | None = None  # NOWE
) -> IntentResult:
    """
    Interpretuj wiadomość W KONTEKŚCIE poprzednich wiadomości.

    Args:
        message: Bieżąca wiadomość użytkownika
        conversation_context: {
            "messages": [...],  # Historia wiadomości
            "extracted_params": {...},  # Już wyekstrahowane parametry
            "last_intent": "social_media_post",  # Ostatni wykryty intent
            "awaiting_recommendations": True,  # Czy czekamy na odpowiedź
        }
    """
    # Jeśli czekamy na odpowiedź (user odpowiada na pytanie)
    if conversation_context and conversation_context.get("awaiting_recommendations"):
        # Użyj ostatniego intent zamiast wykrywać nowy
        last_intent = conversation_context.get("last_intent")
        if last_intent:
            intent = Intent(last_intent)
            # Ekstrakcja tylko nowych parametrów z odpowiedzi
            new_params = self.extract_params_from_message(message, intent)
            # Merge z istniejącymi
            merged_params = {
                **conversation_context.get("extracted_params", {}),
                **new_params
            }
            # Sprawdź czy mamy wszystko
            ...
```

### 1.2 Inteligentne rozpoznawanie odpowiedzi

**Problem:** "casualowy" jest rozpoznawane jako nowy intent (UNKNOWN)

**Rozwiązanie:** Wykryj czy wiadomość to odpowiedź na pytanie

```python
def is_followup_response(self, message: str, context: dict) -> bool:
    """Sprawdź czy wiadomość to odpowiedź na poprzednie pytanie."""

    # Krótkie odpowiedzi to zazwyczaj odpowiedzi
    if len(message.split()) <= 5:
        return True

    # Odpowiedzi na pytania o parametry
    param_values = [
        "profesjonalny", "casualowy", "zabawny", "formalny",  # tone
        "instagram", "facebook", "linkedin",  # platform
        "młodzi", "dorośli", "firmy", "wszyscy",  # audience
    ]
    if message.lower().strip() in param_values:
        return True

    # Jeśli czekamy na rekomendacje
    if context.get("awaiting_recommendations"):
        return True

    return False
```

### 1.3 Aktualizacja conversation_service.py

```python
async def process_message(
    self,
    message: str,
    conversation_context: dict[str, Any],
    company_context: dict[str, Any],
) -> dict[str, Any]:

    # KLUCZOWA ZMIANA: Przekaż kontekst do interpret
    intent_result = await assistant_router.interpret(
        message,
        conversation_context=conversation_context  # <-- TO BRAKOWAŁO!
    )

    # Jeśli to odpowiedź na pytanie, nie zmieniaj intent
    if conversation_context.get("awaiting_recommendations"):
        # Zachowaj poprzedni intent
        intent_result.intent = Intent(conversation_context.get("last_intent"))
        # Merge parametrów
        intent_result.extracted_params = {
            **conversation_context.get("extracted_params", {}),
            **intent_result.extracted_params
        }
```

---

## Faza 2: Agenci jako "Pracownicy" z Osobowością

### 2.1 Agent State Machine

Każdy agent powinien mieć stan i "pamięć roboczą":

```python
class AgentState:
    """Stan agenta w kontekście konwersacji."""

    def __init__(self):
        self.current_task: str | None = None  # "creating_instagram_post"
        self.gathered_params: dict = {}
        self.missing_params: list = []
        self.conversation_stage: str = "idle"  # idle, gathering, confirming, executing
        self.last_question: str | None = None

    def transition(self, event: str):
        """Przejście między stanami."""
        transitions = {
            ("idle", "new_task"): "gathering",
            ("gathering", "params_complete"): "confirming",
            ("confirming", "confirmed"): "executing",
            ("confirming", "modify"): "gathering",
            ("executing", "done"): "idle",
        }
        new_state = transitions.get((self.conversation_stage, event))
        if new_state:
            self.conversation_stage = new_state
```

### 2.2 Conversation Flow Controller

```python
class ConversationFlowController:
    """Kontroler przepływu konwersacji."""

    async def process(self, message: str, context: ConversationContext) -> Response:
        agent_state = context.get_agent_state()

        match agent_state.conversation_stage:
            case "idle":
                return await self._handle_new_request(message, context)

            case "gathering":
                return await self._handle_param_response(message, context)

            case "confirming":
                return await self._handle_confirmation(message, context)

            case "executing":
                return await self._handle_execution_update(message, context)

    async def _handle_param_response(self, message: str, context):
        """Obsługa odpowiedzi na pytanie o parametry."""
        agent_state = context.get_agent_state()

        # Ekstrakcja wartości z odpowiedzi
        extracted = self._extract_param_value(
            message,
            agent_state.last_question,
            agent_state.missing_params
        )

        # Aktualizacja zebranych parametrów
        agent_state.gathered_params.update(extracted)

        # Sprawdź czy mamy wszystko
        still_missing = self._check_missing(agent_state)

        if not still_missing:
            agent_state.transition("params_complete")
            return self._build_confirmation_response(agent_state)
        else:
            # Zadaj następne pytanie
            return self._build_next_question(still_missing[0])
```

### 2.3 Struktura danych konwersacji (MongoDB)

```javascript
{
  "_id": ObjectId("..."),
  "company_id": "...",
  "messages": [...],

  // NOWE: Stan agenta
  "agent_state": {
    "current_task": "instagram_post",
    "conversation_stage": "gathering",
    "gathered_params": {
      "topic": "Dario - aplikacja dla terapeutów...",
      "platform": "instagram"
    },
    "missing_params": ["tone", "target_audience"],
    "last_question": "Jaki styl/ton?",
    "original_request": "Stwórz post na Instagram o nowym produkcie Dario..."
  },

  "context": {
    "extracted_params": {...},
    "last_intent": "social_media_post",
    "awaiting_recommendations": true
  }
}
```

---

## Faza 3: Pamięć Długoterminowa Agentów

### 3.1 Typy pamięci

```
┌─────────────────────────────────────────────────────────────┐
│                    PAMIĘĆ AGENTA                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Working Memory  │  │ Episodic Memory │  │ Semantic    │ │
│  │ (Konwersacja)   │  │ (Historia)      │  │ Memory      │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • Bieżący task  │  │ • Poprzednie    │  │ • Wiedza o  │ │
│  │ • Zebrane params│  │   konwersacje   │  │   firmie    │ │
│  │ • Stan flow     │  │ • Udane posty   │  │ • Brand     │ │
│  │ • Kontekst      │  │ • Feedback      │  │   voice     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Preferencje użytkownika

```python
class UserPreferences:
    """Zapamiętane preferencje użytkownika."""

    # Automatycznie wykrywane z historii
    preferred_tone: str = "profesjonalny"  # Najczęściej wybierany
    preferred_platform: str = "instagram"
    typical_audience: str = "firmy"

    # Eksplicytnie ustawione
    skip_recommendations: bool = False  # "Nie pytaj o szczegóły"
    auto_approve: bool = False

    @classmethod
    async def learn_from_history(cls, company_id: str) -> "UserPreferences":
        """Naucz się preferencji z historii konwersacji."""
        # Analiza poprzednich wyborów użytkownika
        ...
```

---

## Faza 4: Architektura Multi-Agent

### 4.1 Specjalizacja agentów

```
┌────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                               │
│  (Rozumie intent, deleguje do specjalistów, zarządza flow)     │
└────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  CONVERSATION │    │   PARAMETER   │    │   EXECUTION   │
│     AGENT     │    │    AGENT      │    │     AGENT     │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ • Rozumienie  │    │ • Ekstrakcja  │    │ • Instagram   │
│   kontekstu   │    │   parametrów  │    │ • Copywriter  │
│ • Wykrywanie  │    │ • Walidacja   │    │ • Invoice     │
│   intencji    │    │ • Dopytywanie │    │ • HR          │
│ • Odpowiedzi  │    │ • Defaults    │    │ • Legal       │
└───────────────┘    └───────────────┘    └───────────────┘
```

### 4.2 Conversation Agent (LLM-powered)

```python
class ConversationAgent:
    """Agent odpowiedzialny za rozumienie kontekstu i prowadzenie rozmowy."""

    SYSTEM_PROMPT = """
    Jesteś asystentem Agora - platformy AI dla firm.

    TWOJA ROLA:
    - Rozumiesz kontekst całej konwersacji
    - Pamiętasz co użytkownik powiedział wcześniej
    - Prowadzisz naturalną rozmowę po polsku
    - Zbierasz potrzebne informacje

    OBECNY KONTEKST:
    {context}

    ZEBRANE PARAMETRY:
    {params}

    BRAKUJĄCE INFORMACJE:
    {missing}

    ZADANIE:
    Odpowiedz użytkownikowi naturalnie, uwzględniając cały kontekst rozmowy.
    """

    async def process(self, message: str, context: ConversationContext) -> str:
        prompt = self.SYSTEM_PROMPT.format(
            context=context.get_summary(),
            params=context.gathered_params,
            missing=context.missing_params,
        )

        response = await self.llm.chat([
            {"role": "system", "content": prompt},
            *context.messages,
            {"role": "user", "content": message}
        ])

        return response
```

### 4.3 Parameter Extraction Agent

```python
class ParameterAgent:
    """Agent do inteligentnej ekstrakcji parametrów."""

    EXTRACTION_PROMPT = """
    Wyekstrahuj parametry z wiadomości użytkownika.

    KONTEKST ZADANIA: {task_type}
    POPRZEDNIE PARAMETRY: {existing_params}
    BRAKUJĄCE: {missing}

    WIADOMOŚĆ: {message}

    Zwróć JSON z wyekstrahowanymi wartościami.
    Jeśli wiadomość to odpowiedź na pytanie o konkretny parametr,
    przypisz wartość do tego parametru.
    """

    async def extract(self, message: str, context: dict) -> dict:
        # LLM-based extraction dla lepszego rozumienia
        ...
```

---

## Faza 5: Implementacja krok po kroku

### Sprint 1: Naprawa kontekstu (1-2 dni)

- [ ] Przekazać `conversation_context` do `interpret()`
- [ ] Dodać `is_followup_response()` detection
- [ ] Zachować `last_intent` gdy user odpowiada na pytanie
- [ ] Merge parametrów między wiadomościami
- [ ] Testy: konwersacja z dopytywaniem działa

### Sprint 2: Agent State Machine (2-3 dni)

- [ ] Zdefiniować `AgentState` dataclass
- [ ] Zaimplementować state transitions
- [ ] Zapisywać stan w MongoDB
- [ ] `ConversationFlowController` class
- [ ] Testy: przepływ gathering → confirming → executing

### Sprint 3: Conversation Agent (LLM) (3-4 dni)

- [ ] Prompt engineering dla conversation agent
- [ ] Integracja z GPT-4o-mini dla rozumienia kontekstu
- [ ] Fallback do rule-based gdy LLM niedostępny
- [ ] Caching odpowiedzi dla podobnych pytań
- [ ] Testy: naturalny przepływ konwersacji

### Sprint 4: Pamięć i preferencje (2-3 dni)

- [ ] `UserPreferences` model
- [ ] Learning from history
- [ ] "Nie pytaj więcej" option
- [ ] Smart defaults based on history
- [ ] Testy: preferencje są zapamiętywane

### Sprint 5: Polish & UX (1-2 dni)

- [ ] Lepsze komunikaty błędów
- [ ] Progress indicators
- [ ] Undo/modify w trakcie flow
- [ ] Feedback loop

---

## Metryki sukcesu

| Metryka | Obecny stan | Cel |
|---------|-------------|-----|
| Utrata kontekstu | ~80% przy dopytywaniu | <5% |
| Czas do wykonania zadania | 4-5 wiadomości | 2-3 wiadomości |
| User satisfaction (NPS) | ? | >70 |
| Poprawność parametrów | ~60% | >95% |

---

## Quick Fix (DO ZROBIENIA TERAZ)

Minimalna zmiana która naprawi problem:

**`backend/app/api/v1/endpoints/conversations.py`:**

```python
# Gdy user odpowiada na pytanie o rekomendacje
if awaiting_recommendations:
    conversation_context["recommendations_answered"] = True

    # KLUCZOWE: Zachowaj poprzedni intent i parametry!
    # Nie pozwól interpret() nadpisać ich
    response = await conversation_service.process_message(
        message=data.content,
        conversation_context=conversation_context,
        company_context=company_context,
    )

    # Jeśli interpret() zgubił kontekst, przywróć go
    if response.get("intent") == "unknown" or response.get("confidence", 0) < 0.5:
        response["intent"] = context.get("last_intent")
        response["extracted_params"] = {
            **context.get("extracted_params", {}),
            **response.get("extracted_params", {})
        }
        response["can_execute"] = True  # Mamy wszystko co trzeba
```

---

## Podsumowanie

Problem jest fundamentalny - system traktuje każdą wiadomość jako niezależne zapytanie.
Rozwiązanie wymaga:

1. **Natychmiastowo:** Przekazywanie i używanie kontekstu w `interpret()`
2. **Krótkoterminowo:** State machine dla przepływu konwersacji
3. **Średnioterminowo:** LLM-powered conversation agent
4. **Długoterminowo:** Pełna pamięć i personalizacja

Priorytet: **Sprint 1** - naprawa kontekstu jest krytyczna i blokuje użyteczność systemu.

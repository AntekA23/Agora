# Agora

## Opis projektu

**Agora** to platforma SaaS dla małych i średnich przedsiębiorstw (MŚP), zapewniająca dostęp do zespołów wyspecjalizowanych agentów AI. Platforma umożliwia automatyzację zadań biznesowych bez konieczności zatrudniania specjalistów.

## Główne funkcjonalności

### Marketing
- **Instagram Specialist** - generowanie postów, stories i reels z hashtagami
- **Copywriter** - tworzenie treści marketingowych, emaili, opisów produktów

### Finanse
- **Invoice Specialist** - generowanie profesjonalnych faktur z obliczaniem VAT
- **Cashflow Analyst** - analiza przepływów finansowych (planowane)

### System platformy
- Rejestracja i logowanie użytkowników (JWT)
- Zarządzanie firmą i ustawieniami marki
- System zadań z kolejkowaniem i retry
- Dashboard z analityką
- Pamięć agentów (wektorowa baza danych)

## Stack technologiczny

### Backend
- **FastAPI** (Python 3.11+)
- **CrewAI + LangChain** - orkiestracja agentów AI
- **MongoDB** - baza danych
- **Redis + arq** - cache i kolejka zadań
- **Qdrant** - wektorowa baza danych dla pamięci agentów

### Frontend
- **Next.js 14** (App Router)
- **TypeScript** (strict mode)
- **Tailwind CSS + shadcn/ui**
- **Zustand + TanStack Query**

### Infrastruktura
- **Docker Compose** - lokalne środowisko
- **Railway** - produkcja

## Struktura projektu

```
agora/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST API
│   │   ├── core/                # Konfiguracja, security
│   │   ├── models/              # Schematy MongoDB
│   │   ├── schemas/             # Walidacja Pydantic
│   │   └── services/agents/     # Agenci AI
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/                 # Strony Next.js
│       ├── components/          # Komponenty React
│       ├── hooks/               # Custom hooks
│       └── lib/                 # Utilities
└── docker-compose.yml
```

## Zasady projektowe

1. **Prostota** - czysty, czytelny kod
2. **Modularność** - małe, niezależne komponenty
3. **Type Safety** - silne typowanie (Pydantic + TypeScript)
4. **Testowalność** - kod łatwy do testowania
5. **Async-First** - asynchroniczność dla skalowalności

## Język

- Główny język: **Polski**
- Zgodność z polskimi regulacjami (np. VAT)

## Wytyczne dla Claude - System motywów (Dark/Light Mode)

Projekt używa `next-themes` z Tailwind CSS. **ZAWSZE** przestrzegaj poniższych zasad przy tworzeniu/edycji komponentów:

### Konfiguracja

- **Tailwind**: `darkMode: ["class"]` - motyw kontrolowany przez klasę `.dark` na HTML
- **Zmienne CSS**: kolory zdefiniowane w `globals.css` jako zmienne HSL
- **Provider**: `ThemeProvider` w `src/providers/theme-provider.tsx`

### Dostępne zmienne kolorów

| Zmienna | Użycie |
|---------|--------|
| `--background` / `--foreground` | Główne tło i tekst |
| `--card` / `--card-foreground` | Karty i ich zawartość |
| `--primary` / `--primary-foreground` | Przyciski główne, akcenty |
| `--secondary` / `--secondary-foreground` | Elementy drugorzędne |
| `--muted` / `--muted-foreground` | Wyciszone elementy, placeholdery |
| `--accent` / `--accent-foreground` | Wyróżnienia, hover states |
| `--destructive` / `--destructive-foreground` | Błędy, usuwanie |
| `--border` | Obramowania |
| `--input` | Pola formularzy |
| `--ring` | Focus ring |

### Zasady stylowania

**ZAWSZE używaj:**
```tsx
// Tła
className="bg-background"
className="bg-card"
className="bg-muted"

// Teksty
className="text-foreground"
className="text-muted-foreground"
className="text-primary"

// Obramowania
className="border-border"
className="border-input"
```

**NIGDY nie używaj:**
```tsx
// Hardcoded kolory - ZLE!
className="bg-white"
className="bg-gray-900"
className="text-black"
className="text-gray-500"
className="border-gray-200"
```

### Warunkowe style dla motywów

Jeśli potrzebujesz różnych stylów dla dark/light:
```tsx
// Używaj prefiksu dark:
className="bg-white dark:bg-gray-900"  // Tylko gdy zmienne CSS nie wystarczą

// Lub sprawdzaj motyw w komponencie
import { useTheme } from "next-themes";
const { theme } = useTheme();
```

### Komponenty shadcn/ui

Komponenty z `@/components/ui/` są już skonfigurowane dla obu motywów. Używaj ich bez modyfikacji kolorów.

### Checklist przed commitem

- [ ] Brak hardcoded kolorów (`white`, `black`, `gray-*`)
- [ ] Wszystkie tła używają `bg-background`, `bg-card`, `bg-muted`
- [ ] Wszystkie teksty używają `text-foreground`, `text-muted-foreground`
- [ ] Przetestowano w obu motywach (dark i light)

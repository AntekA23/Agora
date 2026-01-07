# Agora

Platforma SaaS dla malych przedsiebiorstw oferujaca zespoly AI agentow-specjalistow.

## Quick Start

### Wymagania
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- OpenAI API Key

### Development

1. Uruchom bazy danych:
```bash
docker-compose up -d
```

2. Backend:
```bash
cd backend
cp .env.example .env
# Uzupelnij OPENAI_API_KEY w .env
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

3. Worker (w osobnym terminalu):
```bash
cd backend
arq app.services.task_queue.WorkerSettings
```

4. Frontend:
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

### Uruchamianie testow

```bash
cd backend
pytest -v
```

## Endpointy API

### Auth
- `POST /api/v1/auth/register` - Rejestracja (tworzy firme i uzytkownika)
- `POST /api/v1/auth/login` - Logowanie
- `POST /api/v1/auth/refresh` - Odswiezenie tokena
- `GET /api/v1/auth/me` - Aktualny uzytkownik

### Users & Companies
- `GET /api/v1/users/me` - Profil uzytkownika
- `PATCH /api/v1/users/me` - Aktualizacja profilu
- `GET /api/v1/companies/me` - Firma uzytkownika
- `PATCH /api/v1/companies/me` - Aktualizacja firmy (w tym brand_voice)

### Marketing Agents
- `POST /api/v1/agents/marketing/instagram` - Generuj post Instagram
- `POST /api/v1/agents/marketing/copywriter` - Generuj tekst marketingowy

### Finance Agents
- `POST /api/v1/finance/invoice` - Analizuj faktury
- `POST /api/v1/finance/cashflow` - Analiza cash flow

### Tasks
- `GET /api/v1/tasks` - Lista zadan (z filtrowaniem: status, department, agent)
- `GET /api/v1/tasks/{id}` - Szczegoly zadania
- `POST /api/v1/tasks/{id}/retry` - Ponow zadanie (dla nieudanych)
- `DELETE /api/v1/tasks/{id}` - Usun zadanie

### Analytics
- `GET /api/v1/analytics/dashboard` - Statystyki dashboard (z cache)

### Health
- `GET /api/v1/health` - Health check (MongoDB, Redis, Qdrant)

## Architektura Agentow

```
Main Coordinator (planowany)
├── Marketing Manager (CrewAI)
│   ├── Instagram Specialist - posty, stories, reels
│   └── Copywriter - teksty reklamowe, emaile, opisy
│
└── Finance Manager (CrewAI)
    ├── Invoice Worker - analiza i kategoryzacja faktur
    └── Cashflow Analyst - analiza przeplywow pienieznych
```

## Funkcjonalnosci

### Zaimplementowane (MVP)
- Rejestracja i logowanie (JWT)
- Onboarding dla nowych uzytkownikow
- Dashboard z analitykami
- Marketing agents (Instagram, Copywriter)
- Finance agents (Invoice, Cashflow)
- Pamiec agentow (Qdrant vector DB)
- Retry dla nieudanych zadan
- Eksport wynikow (kopiowanie, pobieranie)
- Dark/Light mode
- Caching (Redis) dla analytics
- Indeksy MongoDB dla wydajnosci

### Planowane
- HR Manager z agentami
- Integracje z zewnetrznymi API
- Powiadomienia real-time (WebSocket)
- Rozbudowany system uprawnien

## Stack Technologiczny

### Backend
- **Framework:** FastAPI (async)
- **AI Agents:** CrewAI + LangChain
- **Database:** MongoDB (Motor async driver)
- **Cache/Queue:** Redis + arq
- **Vector DB:** Qdrant (pamiec agentow)
- **Auth:** JWT (python-jose)
- **Validation:** Pydantic v2

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **State:** Zustand + TanStack Query
- **Theme:** next-themes

### Infrastructure
- **Local:** Docker Compose (MongoDB, Redis, Qdrant)
- **Production:** Railway

## Struktura Projektu

```
agora/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST endpoints
│   │   ├── core/                # Config, security, exceptions
│   │   ├── models/              # MongoDB models
│   │   ├── schemas/             # Pydantic schemas
│   │   └── services/
│   │       ├── agents/          # CrewAI agents
│   │       ├── database/        # DB connections
│   │       ├── cache.py         # Redis caching
│   │       ├── memory.py        # Agent memory (Qdrant)
│   │       └── task_queue.py    # arq worker
│   └── tests/                   # pytest tests
│
├── frontend/
│   └── src/
│       ├── app/                 # Next.js pages
│       ├── components/          # React components
│       ├── hooks/               # Custom hooks
│       └── lib/                 # Utils, API client
│
└── docker-compose.yml           # Local services
```

## Principia Agory (Zasady)

1. **Prostota** - kod prosty i czytelny
2. **Modularnosc** - male, niezalezne komponenty
3. **Type Safety** - wszedzie typy (Pydantic, TypeScript strict)
4. **Testowalnosc** - kod latwy do testowania
5. **Async First** - wszystko asynchroniczne

## Zmienne Srodowiskowe

### Backend (.env)
```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=agora
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## License

MIT

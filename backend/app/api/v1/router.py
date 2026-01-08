from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    alerts,
    analytics,
    assistant,
    auth,
    campaigns,
    companies,
    dev,
    experiments,
    finance,
    goals,
    health,
    hr,
    integrations,
    legal,
    onboarding,
    sales,
    suggestions,
    support,
    tasks,
    templates,
    users,
    voice,
)

api_router = APIRouter()

# Core
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(companies.router)
api_router.include_router(tasks.router)

# Onboarding (Smart Setup)
api_router.include_router(onboarding.router)

# Assistant (Command Center)
api_router.include_router(assistant.router)

# Templates (One-Click Templates)
api_router.include_router(templates.router)

# Marketing Agents
api_router.include_router(agents.router)
api_router.include_router(campaigns.router)
api_router.include_router(suggestions.router)
api_router.include_router(experiments.router)

# Finance Agents
api_router.include_router(finance.router)

# HR Agents (Phase 3)
api_router.include_router(hr.router)

# Sales Agents (Phase 3)
api_router.include_router(sales.router)

# Legal Agents (Phase 3)
api_router.include_router(legal.router)

# Support Agents (Phase 3)
api_router.include_router(support.router)

# Analytics & Integrations
api_router.include_router(analytics.router)
api_router.include_router(integrations.router)

# Proactive Monitoring (Phase 4)
api_router.include_router(alerts.router)

# Voice Interface (Phase 4)
api_router.include_router(voice.router)

# Autonomous Goals (Phase 5)
api_router.include_router(goals.router)

# Development
api_router.include_router(dev.router)

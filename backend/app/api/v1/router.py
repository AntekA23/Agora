from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    analytics,
    auth,
    campaigns,
    companies,
    dev,
    experiments,
    finance,
    health,
    integrations,
    suggestions,
    tasks,
    users,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(companies.router)
api_router.include_router(agents.router)
api_router.include_router(finance.router)
api_router.include_router(tasks.router)
api_router.include_router(analytics.router)
api_router.include_router(suggestions.router)
api_router.include_router(campaigns.router)
api_router.include_router(integrations.router)
api_router.include_router(experiments.router)
api_router.include_router(dev.router)

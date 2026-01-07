from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.database import mongodb, redis_client
from app.services.database.qdrant import qdrant_service
from app.services.database.indexes import create_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    await mongodb.connect()
    await redis_client.connect()
    try:
        await qdrant_service.connect()
    except Exception:
        pass  # Qdrant is optional

    # Create database indexes for performance
    try:
        await create_indexes(mongodb.db)
    except Exception:
        pass  # Indexes may already exist

    yield
    qdrant_service.disconnect()
    await redis_client.disconnect()
    await mongodb.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"name": settings.APP_NAME, "version": "0.1.0"}

import asyncio
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.database import mongodb, redis_client
from app.services.database.qdrant import qdrant_service
from app.services.database.indexes import create_indexes

# Global reference to worker thread
_worker_thread = None
_worker_stop_event = threading.Event()


def run_arq_worker_sync():
    """Run ARQ worker in a separate thread with its own event loop."""
    from arq import run_worker
    from app.services.task_queue import WorkerSettings

    print("Starting ARQ worker in background thread...")
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_worker(WorkerSettings))
    except Exception as e:
        print(f"ARQ worker error: {e}")
    finally:
        loop.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    global _worker_thread

    # Connect to databases with error handling
    try:
        await mongodb.connect()
        print("MongoDB connected successfully")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")

    try:
        await redis_client.connect()
        print("Redis connected successfully")
    except Exception as e:
        print(f"Redis connection failed: {e}")

    try:
        await qdrant_service.connect()
        print("Qdrant connected successfully")
    except Exception:
        pass  # Qdrant is optional

    # Create database indexes for performance
    try:
        if mongodb.db:
            await create_indexes(mongodb.db)
    except Exception:
        pass  # Indexes may already exist

    # Start ARQ worker in background thread
    try:
        _worker_thread = threading.Thread(target=run_arq_worker_sync, daemon=True)
        _worker_thread.start()
        print("ARQ worker thread started")
    except Exception as e:
        print(f"Failed to start ARQ worker: {e}")

    yield

    # Cleanup
    # Signal worker to stop (daemon thread will be killed automatically)
    _worker_stop_event.set()
    print("ARQ worker stopping...")

    try:
        qdrant_service.disconnect()
    except Exception:
        pass
    try:
        await redis_client.disconnect()
    except Exception:
        pass
    try:
        await mongodb.disconnect()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://frontend-production-0e49.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"name": settings.APP_NAME, "version": "0.1.0"}

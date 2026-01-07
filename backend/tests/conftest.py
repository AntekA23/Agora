import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db() -> AsyncGenerator:
    """Get test database."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = client[f"{settings.MONGODB_DB_NAME}_test"]
    yield database
    # Cleanup after tests
    await client.drop_database(f"{settings.MONGODB_DB_NAME}_test")
    client.close()


@pytest.fixture
def client() -> Generator:
    """Get test client."""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator:
    """Get async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient, db) -> dict:
    """Get auth headers for authenticated requests."""
    # Register a test user
    response = await async_client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User",
            "company_name": "Test Company",
        },
    )

    if response.status_code == 201:
        data = response.json()
        return {"Authorization": f"Bearer {data['access_token']}"}

    # If user exists, login
    response = await async_client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}

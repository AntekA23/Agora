import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_list_tasks_empty(async_client: AsyncClient, auth_headers: dict):
    """Test listing tasks when empty."""
    response = await async_client.get(
        f"{settings.API_V1_PREFIX}/tasks",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


@pytest.mark.asyncio
async def test_list_tasks_with_filters(async_client: AsyncClient, auth_headers: dict):
    """Test listing tasks with filters."""
    response = await async_client.get(
        f"{settings.API_V1_PREFIX}/tasks?department=marketing&status=completed",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data


@pytest.mark.asyncio
async def test_get_nonexistent_task(async_client: AsyncClient, auth_headers: dict):
    """Test getting a task that doesn't exist."""
    response = await async_client.get(
        f"{settings.API_V1_PREFIX}/tasks/507f1f77bcf86cd799439011",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_task(async_client: AsyncClient, auth_headers: dict):
    """Test deleting a task that doesn't exist."""
    response = await async_client.delete(
        f"{settings.API_V1_PREFIX}/tasks/507f1f77bcf86cd799439011",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tasks_require_auth(async_client: AsyncClient):
    """Test that tasks endpoints require authentication."""
    response = await async_client.get(f"{settings.API_V1_PREFIX}/tasks")
    assert response.status_code == 403

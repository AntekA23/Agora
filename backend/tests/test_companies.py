import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_get_my_company(async_client: AsyncClient, auth_headers: dict):
    """Test getting current user's company."""
    response = await async_client.get(
        f"{settings.API_V1_PREFIX}/companies/me",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "slug" in data
    assert "settings" in data
    assert "enabled_agents" in data


@pytest.mark.asyncio
async def test_update_company(async_client: AsyncClient, auth_headers: dict):
    """Test updating company settings."""
    response = await async_client.patch(
        f"{settings.API_V1_PREFIX}/companies/me",
        headers=auth_headers,
        json={
            "industry": "e-commerce",
            "settings": {
                "brand_voice": "friendly and professional",
                "target_audience": "young adults",
                "language": "pl",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["industry"] == "e-commerce"
    assert data["settings"]["brand_voice"] == "friendly and professional"


@pytest.mark.asyncio
async def test_update_company_empty_body(async_client: AsyncClient, auth_headers: dict):
    """Test updating company with empty body fails."""
    response = await async_client.patch(
        f"{settings.API_V1_PREFIX}/companies/me",
        headers=auth_headers,
        json={},
    )

    assert response.status_code == 400

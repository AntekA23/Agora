import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    """Test user registration."""
    response = await async_client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "testpassword123",
            "name": "New User",
            "company_name": "New Company",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    """Test registration with duplicate email fails."""
    # First registration
    await async_client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "name": "First User",
            "company_name": "First Company",
        },
    )

    # Second registration with same email
    response = await async_client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "name": "Second User",
            "company_name": "Second Company",
        },
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """Test successful login."""
    # Register first
    await async_client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "login@example.com",
            "password": "testpassword123",
            "name": "Login User",
            "company_name": "Login Company",
        },
    )

    # Login
    response = await async_client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={
            "email": "login@example.com",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    """Test login with wrong password fails."""
    # Register first
    await async_client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "testpassword123",
            "name": "Wrong Pass User",
            "company_name": "Wrong Pass Company",
        },
    )

    # Login with wrong password
    response = await async_client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient, auth_headers: dict):
    """Test getting current user info."""
    response = await async_client.get(
        f"{settings.API_V1_PREFIX}/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "name" in data


@pytest.mark.asyncio
async def test_protected_route_without_auth(async_client: AsyncClient):
    """Test that protected routes require authentication."""
    response = await async_client.get(f"{settings.API_V1_PREFIX}/auth/me")
    assert response.status_code == 403

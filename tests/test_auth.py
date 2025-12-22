import pytest
from httpx import AsyncClient
from app.schemas.accounts import UserGroupEnum



# ============================================================
# REGISTER
# ============================================================

@pytest.mark.asyncio
async def test_auth_register_success(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "Strong123!"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == "newuser@test.com"
    assert data["is_active"] is False
    assert data["group"] == "USER"


@pytest.mark.asyncio
async def test_auth_register_weak_password(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "weak@test.com",
            "password": "123"
        }
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_auth_register_duplicate_email(
    client: AsyncClient,
    create_user
):
    await create_user(
        "duplicate@test.com",
        "Strong123!",
        UserGroupEnum.USER
    )

    response = await client.post(
        "/auth/register",
        json={
            "email": "duplicate@test.com",
            "password": "Strong123!"
        }
    )

    assert response.status_code == 400


# ============================================================
# LOGIN
# ============================================================

@pytest.mark.asyncio
async def test_auth_login_success(
    client: AsyncClient,
    create_user
):
    await create_user(
        "login@test.com",
        "Strong123!",
        UserGroupEnum.USER
    )

    response = await client.post(
        "/auth/login",
        data={
            "username": "login@test.com",
            "password": "Strong123!"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_auth_login_wrong_password(
    client: AsyncClient,
    create_user
):
    await create_user(
        "wrongpass@test.com",
        "Strong123!",
        UserGroupEnum.USER
    )

    response = await client.post(
        "/auth/login",
        data={
            "username": "wrongpass@test.com",
            "password": "Wrong123!"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect password"

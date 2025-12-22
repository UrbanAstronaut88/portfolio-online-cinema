import pytest
from httpx import AsyncClient
from app.models.accounts import UserGroupEnum


# ============================================================
# GET /users (admin only)
# ============================================================

@pytest.mark.asyncio
async def test_users__reject_without_token(client: AsyncClient):
    """without token - 401"""
    response = await client.get("/users/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_users__reject_non_admin(client: AsyncClient, user_token: str):
    """USER is trying to get a list — 403"""
    response = await client.get(
        "/users/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_users__admin_can_get_list(
    client: AsyncClient,
    admin_token: str,
    basic_user,
    admin_user
):
    """ADMIN receives a list of users"""
    response = await client.get(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "users" in data
    assert data["total"] >= 2

    # user structure
    user = data["users"][0]
    assert "id" in user
    assert "email" in user
    assert "group" in user
    assert user["group"] in ["ADMIN", "USER", "MODERATOR"]


# ============================================================
# Filtering by email
# ============================================================

@pytest.mark.asyncio
async def test_users__filter_by_email(
    client: AsyncClient,
    admin_token: str,
    create_user
):
    await create_user("filter@test.com", "User123!", UserGroupEnum.USER)

    response = await client.get(
        "/users/?email=filter",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    assert any("filter@test.com" == u["email"] for u in data["users"])


# ============================================================
# Filter by group
# ============================================================

@pytest.mark.asyncio
async def test_users__filter_by_group(
    client: AsyncClient,
    admin_token: str,
    create_user
):
    await create_user("mod@test.com", "User123!", UserGroupEnum.MODERATOR)

    response = await client.get(
        "/users/?group=MODERATOR",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    assert all(user["group"] == "MODERATOR" for user in data["users"])


# ============================================================
# Pagination
# ============================================================

@pytest.mark.asyncio
async def test_users__pagination(
    client: AsyncClient,
    admin_token: str,
    create_user
):
    for i in range(5):
        await create_user(f"pg{i}@test.com", "User123!", UserGroupEnum.USER)

    response = await client.get(
        "/users/?skip=0&limit=3",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["users"]) == 3

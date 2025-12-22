import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_certification_create_admin_success(
    client: AsyncClient,
    admin_token: str,
):
    """
    POST /certifications
    ADMIN → success
    """
    response = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "PG-13"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PG-13"
    assert "id" in data


@pytest.mark.asyncio
async def test_certification_create_forbidden_for_user(
    client: AsyncClient,
    user_token: str,
):
    """
    POST /certifications
    USER → forbidden
    """
    response = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "R"
        }
    )

    assert response.status_code == 403

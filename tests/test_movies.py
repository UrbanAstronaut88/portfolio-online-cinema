import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_movies_list_empty(client: AsyncClient):
    """
    GET /movies
    When there are no movies in DB → should return empty list
    """
    response = await client.get("/movies/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_movies_get_not_found(client: AsyncClient):
    """
    GET /movies/{id}
    Non-existing movie → 404
    """
    response = await client.get("/movies/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Movie not found"


@pytest.mark.asyncio
async def test_movies_genres_empty(client: AsyncClient):
    """
    GET /movies/genres
    No genres → empty list
    """
    response = await client.get("/movies/genres")
    assert response.status_code == 200
    assert response.json() == []



@pytest.mark.asyncio
async def test_movies_create_unauthorized(client: AsyncClient):
    """
    POST /movies
    No token → 401
    """
    response = await client.post("/movies/", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_movies_create_forbidden_for_user(
    client: AsyncClient,
    user_token: str,
):
    """
    POST /movies
    USER role → 403
    """
    response = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "Test Movie",
            "year": 2024,
            "time": 120,
            "imdb": 8.1,
            "votes": 1000,
            "description": "Test description",
            "price": 10.0,
            "certification_id": 1,
            "genres": [],
            "directors": [],
            "stars": [],
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized"


@pytest.mark.asyncio
async def test_movies_create_admin_success(
    client: AsyncClient,
    admin_token: str,
):
    """
    POST /movies
    ADMIN → success
    """

    # unique name certification (to avoid UNIQUE constraint)
    cert_name = f"PG-13-{uuid.uuid4().hex[:8]}"

    cert_response = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": cert_name},
    )

    assert cert_response.status_code == 200
    certification_id = cert_response.json()["id"]

    response = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Admin Movie",
            "year": 2024,
            "time": 110,
            "imdb": 7.9,
            "votes": 500,
            "description": "Created by admin",
            "price": 12.5,
            "certification_id": certification_id,
            "genres": [],
            "directors": [],
            "stars": [],
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Admin Movie"
    assert data["certification"]["name"] == cert_name

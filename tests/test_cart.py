import pytest
from httpx import AsyncClient


# -------------------------------------------------
# GET /cart — empty cart
# -------------------------------------------------
@pytest.mark.asyncio
async def test_cart_empty(client: AsyncClient, user_token: str):
    """
    GET /cart
    New user → empty cart
    """
    response = await client.get(
        "/cart/",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []


# -------------------------------------------------
# POST /cart/items — add movie to cart
# -------------------------------------------------
@pytest.mark.asyncio
async def test_cart_add_item_success(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    POST /cart/items
    User can add movie to cart
    """

    # 1️⃣ create certification (admin)
    cert_response = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "PG"}
    )
    assert cert_response.status_code == 200
    certification_id = cert_response.json()["id"]

    # 2️⃣ create movie (admin)
    movie_response = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Cart Movie",
            "year": 2024,
            "time": 120,
            "imdb": 8.1,
            "votes": 1000,
            "description": "Movie for cart test",
            "price": 9.99,
            "certification_id": certification_id,
            "genres": [],
            "directors": [],
            "stars": [],
        }
    )
    assert movie_response.status_code == 200
    movie_id = movie_response.json()["id"]

    # 3️⃣ add to cart (user)
    response = await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["movie_id"] == movie_id


# -------------------------------------------------
# POST /cart/items — duplicate item
# -------------------------------------------------
@pytest.mark.asyncio
async def test_cart_add_duplicate_item(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    POST /cart/items
    Duplicate movie → 400
    """

    # certification
    cert = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "R"}
    )
    cert_id = cert.json()["id"]

    # movie
    movie = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Duplicate Movie",
            "year": 2023,
            "time": 100,
            "imdb": 7.0,
            "votes": 300,
            "description": "Duplicate test",
            "price": 5.0,
            "certification_id": cert_id,
            "genres": [],
            "directors": [],
            "stars": [],
        }
    )
    movie_id = movie.json()["id"]

    # first add
    await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id}
    )

    # second add → error
    response = await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id}
    )

    assert response.status_code == 400


# -------------------------------------------------
# DELETE /cart/items/{id}
# -------------------------------------------------
@pytest.mark.asyncio
async def test_cart_remove_item(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    DELETE /cart/items/{id}
    User removes item from cart
    """

    # certification
    cert = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "G"}
    )
    cert_id = cert.json()["id"]

    # movie
    movie = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Remove Movie",
            "year": 2022,
            "time": 90,
            "imdb": 6.5,
            "votes": 200,
            "description": "Remove test",
            "price": 4.5,
            "certification_id": cert_id,
            "genres": [],
            "directors": [],
            "stars": [],
        }
    )
    movie_id = movie.json()["id"]

    # add
    cart = await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id}
    )
    item_id = cart.json()["items"][0]["id"]

    # remove
    response = await client.delete(
        f"/cart/items/{item_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


# -------------------------------------------------
# DELETE /cart — clear cart
# -------------------------------------------------
@pytest.mark.asyncio
async def test_cart_clear(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    DELETE /cart
    Cart becomes empty
    """

    # certification
    cert = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "NC-17"}
    )
    cert_id = cert.json()["id"]

    # movie
    movie = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Clear Movie",
            "year": 2021,
            "time": 95,
            "imdb": 6.9,
            "votes": 150,
            "description": "Clear cart test",
            "price": 6.0,
            "certification_id": cert_id,
            "genres": [],
            "directors": [],
            "stars": [],
        }
    )
    movie_id = movie.json()["id"]

    # add
    await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id}
    )

    # clear
    response = await client.delete(
        "/cart/",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["items"] == []

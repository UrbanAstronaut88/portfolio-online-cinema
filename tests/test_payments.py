import pytest
from httpx import AsyncClient


# ============================================================
# Helper: create order with a movie (ADMIN creates, USER buys)
# ============================================================

async def prepare_order_with_movie(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
    movie_name: str = "Test Movie"
) -> int:
    """
    ADMIN:
      - creates certification
      - creates movie
    USER:
      - adds a movie to cart
      - creates order
    Returns order_id
    """

    # 1. ADMIN creates certification
    cert_response = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "PG-13"},
    )
    assert cert_response.status_code == 200
    certification_id = cert_response.json()["id"]

    # 2. ADMIN creates movie
    movie_response = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": movie_name,
            "year": 2024,
            "time": 120,
            "imdb": 8.0,
            "votes": 100,
            "description": "Test movie",
            "price": 10.0,
            "certification_id": certification_id,
            "genres": [],
            "directors": [],
            "stars": [],
        },
    )
    assert movie_response.status_code == 200
    movie_id = movie_response.json()["id"]

    # 3. USER adds movie to cart
    cart_response = await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id},
    )
    assert cart_response.status_code == 200

    # 4. USER creates order
    order_response = await client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert order_response.status_code == 200

    return order_response.json()["order_id"]


# ============================================================
# TESTS
# ============================================================

@pytest.mark.asyncio
async def test_payment_create_success(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    POST /payments/{order_id}
    USER → success
    """
    order_id = await prepare_order_with_movie(
        client, admin_token, user_token
    )

    response = await client.post(
        f"/payments/{order_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    assert "client_secret" in response.json()


@pytest.mark.asyncio
async def test_payment_create_forbidden_for_other_user(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    POST /payments/{order_id}
    ADMIN trying to pay user's order → forbidden
    """
    order_id = await prepare_order_with_movie(
        client, admin_token, user_token
    )

    response = await client.post(
        f"/payments/{order_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_refund_payment_admin_success(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    POST /payments/{payment_id}/refund
    ADMIN → success
    """
    order_id = await prepare_order_with_movie(
        client, admin_token, user_token
    )

    # USER initiates payment
    await client.post(
        f"/payments/{order_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    # ADMIN gets payments list
    payments_response = await client.get(
        "/payments/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert payments_response.status_code == 200

    payment_id = payments_response.json()[0]["id"]

    refund_response = await client.post(
        f"/payments/{payment_id}/refund",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert refund_response.status_code == 200
    assert refund_response.json()["message"] == "Refund processed"


@pytest.mark.asyncio
async def test_mock_payment_success_admin(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    POST /payments/mock_success/{payment_id}
    ADMIN → marks payment SUCCESSFUL
    """
    order_id = await prepare_order_with_movie(
        client, admin_token, user_token
    )

    # USER initiates payment
    await client.post(
        f"/payments/{order_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    payments_response = await client.get(
        "/payments/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert payments_response.status_code == 200

    payment_id = payments_response.json()[0]["id"]

    response = await client.post(
        f"/payments/mock_success/{payment_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200

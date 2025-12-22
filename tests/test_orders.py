import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_orders_list_empty(
    client: AsyncClient,
    user_token: str,
):
    """
    GET /orders
    New user → no orders
    """
    response = await client.get(
        "/orders/",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_orders_create_empty_cart(
    client: AsyncClient,
    user_token: str,
):
    """
    POST /orders
    Empty cart → 400
    """
    response = await client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty or invalid items"


@pytest.mark.asyncio
async def test_orders_create_success(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    Full flow:
    ADMIN creates certification + movie
    USER adds movie to cart
    USER creates order
    """

    # create cert (admin)
    cert_response = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "PG-13"}
    )
    assert cert_response.status_code == 200
    certification_id = cert_response.json()["id"]

    # create a movie (admin)
    movie_response = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test Movie",
            "year": 2024,
            "time": 120,
            "imdb": 8.1,
            "votes": 1000,
            "description": "Movie for order test",
            "price": 15.0,
            "certification_id": certification_id,
            "genres": [],
            "directors": [],
            "stars": [],
        }
    )
    assert movie_response.status_code == 200
    movie_id = movie_response.json()["id"]

    # add a movie to cart (user)
    cart_add_response = await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id}
    )
    assert cart_add_response.status_code == 200
    assert len(cart_add_response.json()["items"]) == 1

    # create order (user)
    order_response = await client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert order_response.status_code == 200
    data = order_response.json()

    assert "order_id" in data
    assert "client_secret" in data

    order_id = data["order_id"]

    # orders list should contain the new order
    orders_list_response = await client.get(
        "/orders/",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert orders_list_response.status_code == 200
    orders = orders_list_response.json()

    assert len(orders) == 1
    assert orders[0]["id"] == order_id
    assert orders[0]["status"] == "pending"
    assert orders[0]["total_amount"] == 15.0

    # cart should be empty after order creation
    cart_response = await client.get(
        "/cart/",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []


@pytest.mark.asyncio
async def test_orders_cancel_success(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    USER can cancel own PENDING order
    """

    # create certification
    cert = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "R"}
    )
    certification_id = cert.json()["id"]

    #  create movie
    movie = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Cancelable Movie",
            "year": 2024,
            "time": 100,
            "imdb": 7.0,
            "votes": 200,
            "description": "cancel test",
            "price": 10.0,
            "certification_id": certification_id,
            "genres": [],
            "directors": [],
            "stars": [],
        }
    )
    movie_id = movie.json()["id"]

    # add to cart
    await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id}
    )

    # create order
    order = await client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    order_id = order.json()["order_id"]

    # cancel order
    cancel_response = await client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert cancel_response.status_code == 200
    data = cancel_response.json()

    assert data["status"] == "canceled"


@pytest.mark.asyncio
async def test_orders_cancel_twice_forbidden(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    Cannot cancel already canceled order
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
            "name": "Cancel Twice",
            "year": 2024,
            "time": 90,
            "imdb": 6.5,
            "votes": 100,
            "description": "cancel twice",
            "price": 9.0,
            "certification_id": cert_id,
            "genres": [],
            "directors": [],
            "stars": [],
        }
    )
    movie_id = movie.json()["id"]

    # cart → order
    await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id}
    )
    order = await client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    order_id = order.json()["order_id"]

    # first cancel
    await client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    # second cancel
    second_cancel = await client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert second_cancel.status_code == 400


@pytest.mark.asyncio
async def test_orders_pay_success(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    USER can pay PENDING order
    """

    cert = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "PG"}
    )
    cert_id = cert.json()["id"]

    movie = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Payable Movie",
            "year": 2024,
            "time": 110,
            "imdb": 7.8,
            "votes": 400,
            "description": "payment test",
            "price": 20.0,
            "certification_id": cert_id,
            "genres": [],
            "directors": [],
            "stars": [],
        }
    )
    movie_id = movie.json()["id"]

    await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id}
    )

    order = await client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    order_id = order.json()["order_id"]

    pay_response = await client.post(
        f"/orders/{order_id}/pay",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert pay_response.status_code == 200
    assert "client_secret" in pay_response.json()


@pytest.mark.asyncio
async def test_orders_pay_canceled_forbidden(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
):
    """
    Cannot pay canceled order
    """

    cert = await client.post(
        "/certifications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "X"}
    )
    cert_id = cert.json()["id"]

    movie = await client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Canceled Payment",
            "year": 2024,
            "time": 95,
            "imdb": 6.0,
            "votes": 80,
            "description": "no payment",
            "price": 8.0,
            "certification_id": cert_id,
            "genres": [],
            "directors": [],
            "stars": [],
        }
    )
    movie_id = movie.json()["id"]

    await client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"movie_id": movie_id}
    )

    order = await client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    order_id = order.json()["order_id"]

    await client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    pay_response = await client.post(
        f"/orders/{order_id}/pay",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert pay_response.status_code == 400

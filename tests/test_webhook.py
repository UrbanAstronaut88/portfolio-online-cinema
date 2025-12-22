import os
import pytest
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def enable_mock_webhook():
    """
    Enable MOCK_WEBHOOK for all webhook tests
    """
    os.environ["MOCK_WEBHOOK"] = "True"
    yield
    os.environ["MOCK_WEBHOOK"] = "False"


@pytest.mark.asyncio
async def test_webhook_mock_success(client: AsyncClient):
    """
    POST /webhooks/stripe
    MOCK MODE → success
    """
    response = await client.post(
        "/webhooks/stripe",
        json={"payment_id": "pi_test_123"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "mock success"
    assert data["received_payment_id"] == "pi_test_123"


@pytest.mark.asyncio
async def test_webhook_mock_custom_payment_id(client: AsyncClient):
    """
    Custom payment_id is accepted
    """
    response = await client.post(
        "/webhooks/stripe",
        json={"payment_id": "pi_custom_999"},
    )

    assert response.status_code == 200
    assert response.json()["received_payment_id"] == "pi_custom_999"


@pytest.mark.asyncio
async def test_webhook_mock_without_body(client: AsyncClient):
    """
    Empty body → still works in MOCK mode
    """
    response = await client.post("/webhooks/stripe")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "mock success"
    assert "received_payment_id" in data

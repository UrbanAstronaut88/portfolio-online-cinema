from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import stripe
import os

from app.db.session import get_db
from app.crud.payments import confirm_payment

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

MOCK_WEBHOOK = os.getenv("MOCK_WEBHOOK", "False") == "True"


@router.post(
    "/stripe",
    include_in_schema=True,
    summary="Stripe webhook endpoint",
    description=(
        "Handles Stripe webhook events.\n\n"
        "- In MOCK mode accepts JSON payload\n"
        "- In production validates Stripe signature\n"
        "- Confirms payment asynchronously"
    ),
)
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if MOCK_WEBHOOK:
        try:
            body = await request.json()
        except Exception:
            body = {}

        payment_id = body.get("payment_id", "pi_mock_123")
        background_tasks.add_task(confirm_payment, db, payment_id)

        return {
            "status": "mock success",
            "received_payment_id": payment_id,
        }

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        payment_id = payment_intent["id"]
        background_tasks.add_task(confirm_payment, db, payment_id)

    return {"status": "success"}

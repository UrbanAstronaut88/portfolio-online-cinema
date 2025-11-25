import asyncio
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.accounts import ActivationToken
from datetime import datetime


app = Celery("tasks", broker="redis://localhost:6379/0")  # Redis as a broker


async def cleanup_expired_tokens_async(session: AsyncSession):
    result = await session.execute(
        select(ActivationToken).where(ActivationToken.expires_at < datetime.utcnow())
    )
    expired = result.scalars().all()
    for token in expired:
        await session.delete(token)
    await session.commit()


@app.task
def cleanup_expired_tokens():
    asyncio.run(cleanup_expired_tokens_async(AsyncSessionLocal()))

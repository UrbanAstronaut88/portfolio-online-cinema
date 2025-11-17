from celery import Celery
from app.db.session import SessionLocal
from app.models.accounts import ActivationToken
from datetime import datetime


app = Celery("tasks", broker="redis://localhost:6379/0")  # broker = Redis

@app.task
def cleanup_expired_tokens():
    db = SessionLocal()
    expired = db.query(ActivationToken).filter(ActivationToken.expires_at < datetime.utcnow()).all()
    for token in expired:
        db.delete(token)
    db.commit()
    db.close()

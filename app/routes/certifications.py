from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.movies import Certification
from app.schemas.movies import Certification as CertificationSchema, CertificationCreate
from app.utils.auth import get_current_user
from app.models.accounts import User

router = APIRouter(prefix="/certifications", tags=["certifications"])


@router.post("/", response_model=CertificationSchema)
async def create_certification(
    data: CertificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.group.name != "ADMIN":
        raise HTTPException(403, "Not authorized")

    cert = Certification(name=data.name)
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    return cert

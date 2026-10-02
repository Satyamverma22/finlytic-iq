# app/consent/dependencies.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.consent.service import has_active_consent
from app.core.database import get_db


def require_consent(purpose: str):
    async def checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        if not await has_active_consent(db, current_user.id, purpose):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Consent required for '{purpose}'. Grant it in the Consent Center to use this feature.",
            )
        return current_user

    return checker
# app/consent/service.py

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.consent.models import Consent

PURPOSE_DATA_TYPES = {
    "financial_analysis": "Transactions, income, loans, and savings",
    "fraud_analysis": "Messages submitted for scam analysis",
    "personalised_recommendations": "Profile details used for scheme matching",
    "anonymous_analytics": "Anonymised aggregate financial data",
}


class ConsentAlreadyGrantedError(Exception):
    pass


class ConsentNotFoundError(Exception):
    pass


def consent_status(consent: Consent) -> str:
    if consent.revoked_at is not None:
        return "revoked"
    if consent.expires_at is not None and consent.expires_at <= datetime.now(timezone.utc):
        return "expired"
    return "active"


async def list_consents(db: AsyncSession, user_id) -> list[Consent]:
    result = await db.execute(
        select(Consent).where(Consent.user_id == user_id).order_by(Consent.granted_at.desc())
    )
    return list(result.scalars().all())


async def has_active_consent(db: AsyncSession, user_id, purpose: str) -> bool:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Consent.id).where(
            Consent.user_id == user_id,
            Consent.purpose == purpose,
            Consent.revoked_at.is_(None),
            or_(Consent.expires_at.is_(None), Consent.expires_at > now),
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def grant_consent(
    db: AsyncSession, user_id, purpose: str, expires_in_days: int | None
) -> Consent:
    if await has_active_consent(db, user_id, purpose):
        raise ConsentAlreadyGrantedError()

    consent = Consent(
        user_id=user_id,
        purpose=purpose,
        data_type=PURPOSE_DATA_TYPES[purpose],
        expires_at=(
            datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            if expires_in_days else None
        ),
    )
    db.add(consent)
    await db.commit()
    await db.refresh(consent)
    return consent


async def revoke_consent(db: AsyncSession, user_id, consent_id: uuid.UUID) -> Consent:
    result = await db.execute(
        select(Consent).where(Consent.id == consent_id, Consent.user_id == user_id)
    )
    consent = result.scalar_one_or_none()
    if consent is None:
        raise ConsentNotFoundError()

    if consent.revoked_at is None:
        consent.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(consent)
    return consent
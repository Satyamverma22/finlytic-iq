# app/consent/router.py

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.consent import service
from app.consent.models import Consent
from app.consent.schemas import ConsentGrantRequest, ConsentResponse
from app.core.database import get_db
from app.audit.service import record_audit

router = APIRouter(prefix="/api/consents", tags=["consent"])


def _to_response(c: Consent) -> ConsentResponse:
    return ConsentResponse(
        id=c.id,
        purpose=c.purpose,
        data_type=c.data_type,
        recipient=c.recipient,
        granted_at=c.granted_at,
        expires_at=c.expires_at,
        revoked_at=c.revoked_at,
        status=service.consent_status(c),
    )


@router.get("", response_model=list[ConsentResponse])
async def list_consents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return [_to_response(c) for c in await service.list_consents(db, current_user.id)]


@router.post("", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def grant_consent(
    payload: ConsentGrantRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        consent = await service.grant_consent(
            db, current_user.id, payload.purpose, payload.expires_in_days
        )
    except service.ConsentAlreadyGrantedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active consent for this purpose already exists.",
        )

    await record_audit(
        db,
        "consent.granted",
        user_id=current_user.id,
        resource_type="consent",
        resource_id=str(consent.id),
        details={"purpose": payload.purpose},
        request=request,
    )

    return _to_response(consent)


@router.patch("/{consent_id}/revoke", response_model=ConsentResponse)
async def revoke_consent(
    consent_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        consent = await service.revoke_consent(db, current_user.id, consent_id)
    except service.ConsentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found.",
        )

    await record_audit(
        db,
        "consent.revoked",
        user_id=current_user.id,
        resource_type="consent",
        resource_id=str(consent.id),
        details={"purpose": consent.purpose},
        request=request,
    )

    return _to_response(consent)
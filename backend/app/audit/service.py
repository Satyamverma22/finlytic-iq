# app/audit/service.py

import logging

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog

logger = logging.getLogger("audit")


async def record_audit(
    db: AsyncSession,
    action: str,
    user_id=None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    request: Request | None = None,
) -> None:
    """Call AFTER the main operation has committed. Never pass sensitive
    data in `details`. A failed audit write is logged but doesn't break the request."""
    try:
        db.add(AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.client.host if request and request.client else None,
        ))
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("Failed to write audit log for action %s", action)
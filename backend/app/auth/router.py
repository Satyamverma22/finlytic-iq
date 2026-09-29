# app/auth/router.py

from app.auth.models import User

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.schemas import UserRegister, UserLogin, UserResponse, Token
from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token
from app.core.database import get_db
from app.audit.service import record_audit
from app.shared.pii import mask_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await service.register_user(db, payload)
    except service.EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    await record_audit(
        db,
        "auth.register",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        request=request,
    )

    return user


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await service.authenticate_user(
            db,
            payload.email,
            payload.password,
        )
    except service.InvalidCredentialsError:
        await record_audit(
            db,
            "auth.login.failed",
            details={
                "email_hint": mask_email(payload.email),
            },
            request=request,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    await record_audit(
        db,
        "auth.login.success",
        user_id=user.id,
        request=request,
    )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
        }
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
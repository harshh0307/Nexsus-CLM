from datetime import datetime, timedelta, timezone

_naive_utc = lambda: datetime.now(timezone.utc).replace(tzinfo=None)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.config import settings
from app.db.engine import get_session
from app.db.models import PasswordResetToken, User
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.security.auth import (
    create_access_token,
    generate_reset_token,
    get_current_user,
    hash_password,
    verify_password,
    verify_reset_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session=Depends(get_session)):
    if len(body.password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters")

    stmt = select(User).where(User.email == body.email)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(str(user.id), user.email)
    return AuthResponse(access_token=token, user_id=str(user.id), email=user.email, name=user.name)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, session=Depends(get_session)):
    stmt = select(User).where(User.email == body.email)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(str(user.id), user.email)
    return AuthResponse(access_token=token, user_id=str(user.id), email=user.email, name=user.name)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(body: ForgotPasswordRequest, session=Depends(get_session)):
    stmt = select(User).where(User.email == body.email)
    user = (await session.execute(stmt)).scalar_one_or_none()

    response = ForgotPasswordResponse(message="If email exists, a reset link has been sent.")

    if not user:
        return response

    raw_token, hashed_token = generate_reset_token()
    expires_at = _naive_utc() + timedelta(minutes=settings.reset_token_expire_minutes)

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=hashed_token,
        expires_at=expires_at,
    )
    session.add(reset_record)
    await session.commit()

    if settings.dev_mode:
        response.dev_token = raw_token

    return response


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(body: ResetPasswordRequest, session=Depends(get_session)):
    stmt = select(PasswordResetToken).where(
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > _naive_utc(),
    )
    tokens = (await session.execute(stmt)).scalars().all()

    matched = None
    for t in tokens:
        if verify_reset_token(body.token, t.token_hash):
            matched = t
            break

    if not matched:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user_stmt = select(User).where(User.id == matched.user_id)
    user = (await session.execute(user_stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.password_hash = hash_password(body.new_password)
    matched.used_at = _naive_utc()
    await session.commit()

    return ResetPasswordResponse(message="Password reset successful")


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email, "name": user.name}

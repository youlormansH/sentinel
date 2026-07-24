from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.db.session import get_db
from app.models.session import Session as UserSession
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MfaDisableRequest,
    MfaEnableRequest,
    MfaSetupResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionOut,
    TokenPair,
    VerifyEmailRequest,
)
from app.schemas.user import UserOut
from app.services import auth_service
from app.services.request_meta import extract_request_meta

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(
        db, email=payload.email, full_name=payload.full_name, password=payload.password
    )
    return UserOut.model_validate(user)


@router.post("/verify-email", status_code=204)
async def verify_email(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.verify_email(db, payload.token)


@router.post("/login", response_model=TokenPair)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    meta = extract_request_meta(request)
    result = await auth_service.authenticate(
        db, email=payload.email, password=payload.password, mfa_code=payload.mfa_code, meta=meta
    )
    if result["mfa_required"]:
        return TokenPair(access_token="", refresh_token="", mfa_required=True)

    tokens = await auth_service.issue_token_pair(db, user=result["user"], meta=meta)
    return TokenPair(**tokens, mfa_required=False)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    tokens = await auth_service.refresh_access_token(db, refresh_token=payload.refresh_token)
    return TokenPair(**tokens, mfa_required=False)


@router.post("/logout", status_code=204)
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.logout(db, refresh_token=payload.refresh_token)


@router.post("/forgot-password", status_code=204)
@limiter.limit("5/minute")
async def forgot_password(request: Request, payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.request_password_reset(db, email=payload.email)


@router.post("/reset-password", status_code=204)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.reset_password(db, token=payload.token, new_password=payload.new_password)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def mfa_setup(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await auth_service.setup_mfa(db, user=user)
    return MfaSetupResponse(**result)


@router.post("/mfa/enable", status_code=204)
async def mfa_enable(
    payload: MfaEnableRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await auth_service.enable_mfa(db, user=user, code=payload.code)


@router.post("/mfa/disable", status_code=204)
async def mfa_disable(
    payload: MfaDisableRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await auth_service.disable_mfa(db, user=user, code=payload.code)


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == user.id, UserSession.revoked.is_(False))
        .order_by(UserSession.created_at.desc())
    )
    return [SessionOut.model_validate(s) for s in result.scalars().all()]


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_session(session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = await db.get(UserSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    session.revoked = True
    await db.commit()

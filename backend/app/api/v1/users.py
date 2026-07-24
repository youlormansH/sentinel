import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.core.permissions import MANAGE_USERS, VIEW_USERS
from app.core.security import hash_password
from app.db.session import get_db
from app.models.rbac import Role
from app.models.user import User
from app.schemas.common import Page
from app.schemas.user import AdminResetPasswordRequest, UserCreateRequest, UserOut, UserUpdateRequest
from app.services.audit_service import write_audit_log
from app.services.request_meta import extract_request_meta

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserOut])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    role: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions(VIEW_USERS)),
):
    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where((User.email.ilike(pattern)) | (User.full_name.ilike(pattern)))
        count_stmt = count_stmt.where((User.email.ilike(pattern)) | (User.full_name.ilike(pattern)))

    if role:
        stmt = stmt.join(Role).where(Role.name == role)
        count_stmt = count_stmt.join(Role).where(Role.name == role)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    users = (await db.execute(stmt)).scalars().all()

    return Page(
        items=[UserOut.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    request: Request,
    payload: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(MANAGE_USERS)),
):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    role_result = await db.execute(select(Role).where(Role.name == payload.role))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail=f"Unknown role: {payload.role}")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role_id=role.id,
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    meta = extract_request_meta(request)
    await write_audit_log(
        db,
        action="user.created",
        category="user_management",
        user_id=admin.id,
        user_email=admin.email,
        ip_address=meta.ip_address,
        device=meta.device,
        browser=meta.browser,
        details=f"Created user {user.email} with role {role.name}",
    )
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    request: Request,
    user_id: str,
    payload: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(MANAGE_USERS)),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = []
    if payload.full_name is not None:
        user.full_name = payload.full_name
        changes.append("full_name")
    if payload.role is not None:
        role_result = await db.execute(select(Role).where(Role.name == payload.role))
        role = role_result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=400, detail=f"Unknown role: {payload.role}")
        user.role_id = role.id
        changes.append(f"role -> {payload.role}")
    if payload.is_active is not None:
        user.is_active = payload.is_active
        changes.append(f"is_active -> {payload.is_active}")

    await db.commit()
    await db.refresh(user)

    meta = extract_request_meta(request)
    await write_audit_log(
        db,
        action="user.updated",
        category="user_management",
        user_id=admin.id,
        user_email=admin.email,
        ip_address=meta.ip_address,
        device=meta.device,
        browser=meta.browser,
        details=f"Updated user {user.email}: {', '.join(changes) or 'no changes'}",
    )
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    request: Request,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(MANAGE_USERS)),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    email = user.email
    await db.delete(user)

    meta = extract_request_meta(request)
    await write_audit_log(
        db,
        action="user.deleted",
        category="user_management",
        user_id=admin.id,
        user_email=admin.email,
        ip_address=meta.ip_address,
        device=meta.device,
        browser=meta.browser,
        details=f"Deleted user {email}",
    )


@router.post("/{user_id}/reset-password", status_code=204)
async def admin_reset_password(
    request: Request,
    user_id: str,
    payload: AdminResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(MANAGE_USERS)),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    await db.commit()

    meta = extract_request_meta(request)
    await write_audit_log(
        db,
        action="user.password_reset_by_admin",
        category="user_management",
        user_id=admin.id,
        user_email=admin.email,
        ip_address=meta.ip_address,
        device=meta.device,
        browser=meta.browser,
        details=f"Reset password for {user.email}",
    )

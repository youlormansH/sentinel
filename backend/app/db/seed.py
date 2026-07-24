"""Idempotent seed: RBAC roles/permissions + a first admin user.

Run with `python -m app.db.seed` (also invoked automatically from the
Docker Compose entrypoint on first boot).
"""
import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.permissions import ALL_PERMISSIONS, ROLE_DESCRIPTIONS, ROLE_PERMISSIONS
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.rbac import Permission, Role
from app.models.user import User


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # Permissions
        code_to_permission: dict[str, Permission] = {}
        for code, description in ALL_PERMISSIONS.items():
            result = await db.execute(select(Permission).where(Permission.code == code))
            permission = result.scalar_one_or_none()
            if not permission:
                permission = Permission(code=code, description=description)
                db.add(permission)
                await db.flush()
            code_to_permission[code] = permission

        # Roles
        name_to_role: dict[str, Role] = {}
        for role_name, permission_codes in ROLE_PERMISSIONS.items():
            permissions = [code_to_permission[code] for code in permission_codes]
            result = await db.execute(select(Role).where(Role.name == role_name))
            role = result.scalar_one_or_none()
            if not role:
                # Set permissions at construction time: assigning to the relationship
                # attribute *after* flush would trigger a lazy-load re-fetch of the
                # (empty) current collection, which needs a sync DB round-trip that
                # isn't safe to run inline on an AsyncSession.
                role = Role(name=role_name, description=ROLE_DESCRIPTIONS[role_name], permissions=permissions)
                db.add(role)
                await db.flush()
            else:
                role.permissions = permissions
            name_to_role[role_name] = role

        await db.commit()

        # First admin user
        result = await db.execute(select(User).where(User.email == settings.FIRST_ADMIN_EMAIL))
        admin = result.scalar_one_or_none()
        if not admin:
            admin_role_result = await db.execute(select(Role).where(Role.name == "admin"))
            admin_role = admin_role_result.scalar_one()
            admin = User(
                email=settings.FIRST_ADMIN_EMAIL,
                full_name="Sentinel Admin",
                password_hash=hash_password(settings.FIRST_ADMIN_PASSWORD),
                role_id=admin_role.id,
                is_active=True,
                is_email_verified=True,
            )
            db.add(admin)
            await db.commit()
            print(f"Created first admin user: {settings.FIRST_ADMIN_EMAIL}")
        else:
            print("Admin user already exists; skipping.")

        print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())

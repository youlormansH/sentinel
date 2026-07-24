import pytest
from sqlalchemy import select

from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.models.rbac import Role
from app.models.user import User


async def register_and_login(client, email, password="StrongPass123!"):
    await client.post(
        "/api/v1/auth/register", json={"email": email, "full_name": "Test", "password": password}
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()


async def promote_role(session_factory, email: str, role_name: str) -> None:
    async with session_factory() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one()
        role = (await db.execute(select(Role).where(Role.name == role_name))).scalar_one()
        user.role_id = role.id
        await db.commit()


@pytest.mark.anyio
async def test_admin_can_list_users(client, session_factory):
    tokens = await register_and_login(client, "admin1@example.com")
    await promote_role(session_factory, "admin1@example.com", ROLE_ADMIN)

    # Re-login so the JWT role claim and permission lookups reflect the promotion.
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "admin1@example.com", "password": "StrongPass123!"}
    )
    tokens = resp.json()

    resp = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.anyio
async def test_analyst_can_manage_alerts_but_not_users(client, session_factory):
    tokens = await register_and_login(client, "analyst1@example.com")
    await promote_role(session_factory, "analyst1@example.com", ROLE_ANALYST)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "analyst1@example.com", "password": "StrongPass123!"}
    )
    tokens = resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(
        "/api/v1/alerts",
        json={"severity": "high", "category": "manual", "description": "Analyst-created alert"},
        headers=headers,
    )
    assert resp.status_code == 201

    # Analysts can look up users while investigating (VIEW_USERS)...
    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 200

    # ...but cannot create/manage them (MANAGE_USERS is admin-only).
    resp = await client.post(
        "/api/v1/users",
        json={"email": "new@example.com", "full_name": "New", "password": "StrongPass123!", "role": "user"},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_plain_user_cannot_manage_alerts(client):
    tokens = await register_and_login(client, "plain2@example.com")
    resp = await client.post(
        "/api/v1/alerts",
        json={"severity": "low", "category": "manual", "description": "should fail"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 403

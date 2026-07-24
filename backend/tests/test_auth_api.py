import pytest


async def register_and_login(client, email="analyst@example.com", password="StrongPass123!"):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": password},
    )
    assert resp.status_code == 201, resp.text

    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.anyio
async def test_register_rejects_weak_password(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "full_name": "Weak", "password": "alllowercase"},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_register_and_login_returns_tokens(client):
    tokens = await register_and_login(client)
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["mfa_required"] is False


@pytest.mark.anyio
async def test_login_wrong_password_fails(client):
    await register_and_login(client, email="badpass@example.com")
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "badpass@example.com", "password": "WrongPassword1!"}
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_me_requires_valid_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    tokens = await register_and_login(client, email="me@example.com")
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"
    assert resp.json()["role"] == "user"


@pytest.mark.anyio
async def test_refresh_token_rotates_and_old_refresh_fails(client):
    tokens = await register_and_login(client, email="refresh@example.com")
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["access_token"] != tokens["access_token"]

    # The rotated-out refresh token must no longer work.
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_logout_revokes_session(client):
    tokens = await register_and_login(client, email="logout@example.com")
    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 204

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_regular_user_cannot_list_users(client):
    tokens = await register_and_login(client, email="plainuser@example.com")
    resp = await client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert resp.status_code == 403

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.permissions import ROLE_USER
from app.core.security import hash_password
from app.models.alert import Alert
from app.models.login_attempt import LoginAttempt
from app.models.rbac import Role
from app.models.user import User
from app.services.geo import GeoLocation
from app.services.threat_detection import check_api_abuse, check_brute_force, check_impossible_travel


async def make_user(session_factory, email="victim@example.com") -> str:
    async with session_factory() as db:
        role = (await db.execute(select(Role).where(Role.name == ROLE_USER))).scalar_one()
        user = User(email=email, full_name="Victim", password_hash=hash_password("x"), role_id=role.id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user.id


@pytest.mark.anyio
async def test_brute_force_not_triggered_below_threshold(session_factory):
    async with session_factory() as db:
        for _ in range(5):
            db.add(LoginAttempt(email="x@example.com", success=False, ip_address="1.2.3.4"))
        await db.commit()
        alert = await check_brute_force(db, email="x@example.com", ip_address="1.2.3.4")
        assert alert is None


@pytest.mark.anyio
async def test_brute_force_triggers_at_threshold(session_factory):
    async with session_factory() as db:
        for _ in range(10):
            db.add(LoginAttempt(email="x@example.com", success=False, ip_address="9.9.9.9"))
        await db.commit()
        alert = await check_brute_force(db, email="x@example.com", ip_address="9.9.9.9")
        assert alert is not None
        assert alert.severity == "critical"
        assert alert.category == "brute_force"

        count = (await db.execute(select(Alert))).scalars().all()
        assert len(count) == 1


@pytest.mark.anyio
async def test_impossible_travel_flags_fast_cross_country_login(session_factory):
    user_id = await make_user(session_factory, "traveler@example.com")

    async with session_factory() as db:
        user = await db.get(User, user_id)
        now = datetime.now(timezone.utc)

        houston = LoginAttempt(
            email=user.email, user_id=user.id, success=True, ip_address="1.1.1.1",
            country="United States", city="Houston", latitude=29.7604, longitude=-95.3698,
            created_at=now - timedelta(minutes=5),
        )
        db.add(houston)
        # A second successful attempt is required so the "previous" login (offset 1) resolves to Houston.
        placeholder = LoginAttempt(
            email=user.email, user_id=user.id, success=True, ip_address="1.1.1.1",
            country="United States", city="Houston", latitude=29.7604, longitude=-95.3698,
            created_at=now - timedelta(minutes=4, seconds=59),
        )
        db.add(placeholder)
        await db.commit()

        user.last_login_at = now - timedelta(minutes=5)
        user.last_login_country = "United States"
        await db.commit()

        tokyo = GeoLocation(city="Tokyo", country="Japan", latitude=35.6762, longitude=139.6503)
        alert = await check_impossible_travel(
            db, user=user, new_location=tokyo, login_time=now, ip_address="2.2.2.2"
        )
        assert alert is not None
        assert alert.category == "impossible_travel"
        assert "Tokyo" in alert.description


@pytest.mark.anyio
async def test_impossible_travel_allows_plausible_same_city_login(session_factory):
    user_id = await make_user(session_factory, "local@example.com")

    async with session_factory() as db:
        user = await db.get(User, user_id)
        now = datetime.now(timezone.utc)

        for offset in (5, 4):
            db.add(
                LoginAttempt(
                    email=user.email, user_id=user.id, success=True, ip_address="1.1.1.1",
                    country="United States", city="Houston", latitude=29.7604, longitude=-95.3698,
                    created_at=now - timedelta(minutes=offset),
                )
            )
        await db.commit()
        user.last_login_at = now - timedelta(minutes=5)
        user.last_login_country = "United States"
        await db.commit()

        houston_again = GeoLocation(city="Houston", country="United States", latitude=29.76, longitude=-95.37)
        alert = await check_impossible_travel(
            db, user=user, new_location=houston_again, login_time=now, ip_address="1.1.1.1"
        )
        assert alert is None


@pytest.mark.anyio
async def test_api_abuse_triggers_above_threshold(session_factory):
    from app.models.login_attempt import ApiRequestLog

    async with session_factory() as db:
        for _ in range(300):
            db.add(ApiRequestLog(ip_address="5.5.5.5", method="GET", path="/api/v1/logs", status_code=200))
        await db.commit()
        alert = await check_api_abuse(db, user_id=None, ip_address="5.5.5.5")
        assert alert is not None
        assert alert.category == "api_abuse"

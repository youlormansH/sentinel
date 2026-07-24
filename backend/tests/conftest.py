
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.limiter import limiter
from app.core.permissions import ALL_PERMISSIONS, ROLE_DESCRIPTIONS, ROLE_PERMISSIONS
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.rbac import Permission, Role

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def seed_rbac(session_factory):
    async with session_factory() as db:
        code_to_permission = {}
        for code, description in ALL_PERMISSIONS.items():
            permission = Permission(code=code, description=description)
            db.add(permission)
            code_to_permission[code] = permission
        await db.flush()

        for role_name, codes in ROLE_PERMISSIONS.items():
            role = Role(name=role_name, description=ROLE_DESCRIPTIONS[role_name])
            role.permissions = [code_to_permission[c] for c in codes]
            db.add(role)
        await db.commit()


@pytest_asyncio.fixture
async def client(session_factory):
    async def override_get_db():
        async with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    original_sessionmaker = app.state.db_sessionmaker
    app.state.db_sessionmaker = session_factory
    limiter.reset()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    app.state.db_sessionmaker = original_sessionmaker


@pytest.fixture
def anyio_backend():
    return "asyncio"

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.limiter import limiter
from app.core.middleware import ApiActivityMiddleware
from app.db.session import AsyncSessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_sessionmaker = AsyncSessionLocal
    yield


app = FastAPI(
    title="Sentinel API",
    description="Cloud Security & Threat Detection Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.state.db_sessionmaker = AsyncSessionLocal
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiActivityMiddleware)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}

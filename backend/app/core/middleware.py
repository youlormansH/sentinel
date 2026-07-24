import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.security import decode_token
from app.models.login_attempt import ApiRequestLog
from app.services.request_meta import extract_request_meta
from app.services.threat_detection import check_api_abuse

# Paths that don't need to be recorded as "API activity" (docs, health, static assets).
_EXCLUDED_PREFIXES = ("/docs", "/openapi.json", "/redoc", "/health", "/ws")


class ApiActivityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        path = request.url.path
        if not path.startswith(_EXCLUDED_PREFIXES):
            await self._record(request, response.status_code, duration_ms)

        return response

    async def _record(self, request: Request, status_code: int, duration_ms: float) -> None:
        meta = extract_request_meta(request)
        user_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            try:
                payload = decode_token(auth_header[7:])
                if payload.get("type") == "access":
                    user_id = payload.get("sub")
            except ValueError:
                pass

        session_factory = request.app.state.db_sessionmaker
        async with session_factory() as db:
            db.add(
                ApiRequestLog(
                    user_id=user_id,
                    ip_address=meta.ip_address,
                    method=request.method,
                    path=request.url.path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                )
            )
            await db.commit()
            await check_api_abuse(db, user_id=user_id, ip_address=meta.ip_address)

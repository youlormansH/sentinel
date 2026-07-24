from fastapi import APIRouter

from app.api.v1 import ai, alerts, auth, dashboard, logs, users, ws

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(logs.router)
api_router.include_router(alerts.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)
api_router.include_router(ws.router)

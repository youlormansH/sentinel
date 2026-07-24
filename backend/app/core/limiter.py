import redis as redis_sync
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def _resolve_storage_uri() -> str:
    """Use Redis (shared across API replicas) when reachable; otherwise fall
    back to in-process memory so local dev/tests work without a Redis
    instance running."""
    try:
        client = redis_sync.from_url(settings.REDIS_URL, socket_connect_timeout=0.2)
        client.ping()
        return settings.REDIS_URL
    except Exception:
        return "memory://"


limiter = Limiter(key_func=get_remote_address, storage_uri=_resolve_storage_uri())

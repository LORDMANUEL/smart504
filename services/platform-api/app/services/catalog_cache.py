from __future__ import annotations

from redis import Redis
from redis.exceptions import RedisError

from app.config import get_settings


CATALOG_CACHE_VERSION_KEY = "smartdiag:catalog:version"


def catalog_cache_version(client: Redis | None) -> str:
    if client is None:
        return "0"
    try:
        value = client.get(CATALOG_CACHE_VERSION_KEY)
        return value.decode() if isinstance(value, bytes) else str(value or "0")
    except RedisError:
        return "0"


def invalidate_public_catalog_cache() -> None:
    """Atomically move readers to a fresh namespace after an admin mutation."""
    settings = get_settings()
    if not settings.redis_url:
        return
    try:
        Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1).incr(CATALOG_CACHE_VERSION_KEY)
    except RedisError:
        # Cache failure must not roll back an already committed catalog change.
        return

from __future__ import annotations

import hashlib
import hmac
import ipaddress

from fastapi import HTTPException, Request, status
from redis import Redis
from redis.exceptions import RedisError

from app.config import Settings


def trusted_client_key(request: Request, settings: Settings) -> str:
    """Return a non-reversible limiter key from the proxy-validated client address."""
    address = request.client.host if request.client else "unknown"
    try:
        peer = ipaddress.ip_address(address)
        trusted_cdn = any(peer in ipaddress.ip_network(cidr) for cidr in settings.trusted_cdn_cidrs)
    except ValueError:
        trusted_cdn = False
    if trusted_cdn:
        candidate = request.headers.get("cf-connecting-ip", "")
        try:
            address = str(ipaddress.ip_address(candidate))
        except ValueError:
            pass
    digest = hmac.new(
        settings.event_hmac_secret.get_secret_value().encode(),
        address.encode(),
        hashlib.sha256,
    ).hexdigest()
    return digest[:32]


def reject_honeypot(value: str | None) -> None:
    if value and value.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Solicitud no valida")


def enforce_public_limit(
    request: Request,
    settings: Settings,
    *,
    surface: str,
    limit: int,
    window_seconds: int = 60,
) -> None:
    """Atomic, replica-safe public admission control backed by Valkey/Redis."""
    if not settings.redis_url:
        if settings.production:
            raise HTTPException(status_code=503, detail="Proteccion publica no disponible")
        return
    key = f"smartdiag:public-limit:{surface}:{trusted_client_key(request, settings)}"
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        count = client.incr(key)
        if count == 1:
            client.expire(key, window_seconds)
    except RedisError as exc:
        if settings.production:
            raise HTTPException(status_code=503, detail="Proteccion publica no disponible") from exc
        return
    if count > limit:
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes; intente nuevamente mas tarde")

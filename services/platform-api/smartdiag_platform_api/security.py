from __future__ import annotations

import hashlib
import hmac


def sign_body(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_body_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not signature or not secret:
        return False
    expected = sign_body(body, secret)
    return hmac.compare_digest(expected, signature.strip())

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet

from app.config import Settings


def _fernet(settings: Settings) -> Fernet:
    digest = hashlib.sha256(settings.staff_signing_secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def create_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def encrypt_totp_secret(secret: str, settings: Settings) -> str:
    return _fernet(settings).encrypt(secret.encode("ascii")).decode("ascii")


def decrypt_totp_secret(encrypted: str, settings: Settings) -> str:
    return _fernet(settings).decrypt(encrypted.encode("ascii")).decode("ascii")


def totp_code(secret: str, *, timestamp: int | None = None) -> str:
    timestamp = int(time.time()) if timestamp is None else timestamp
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    counter = timestamp // 30
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"


def verify_totp(secret: str, code: str) -> bool:
    candidate = code.strip()
    if len(candidate) != 6 or not candidate.isdigit():
        return False
    now = int(time.time())
    return any(hmac.compare_digest(totp_code(secret, timestamp=now + drift), candidate) for drift in (-30, 0, 30))


def totp_uri(*, secret: str, email: str, issuer: str = "SmartDiag504") -> str:
    return (
        f"otpauth://totp/{quote(issuer)}:{quote(email)}?"
        f"secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"
    )

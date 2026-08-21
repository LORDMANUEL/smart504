from __future__ import annotations

import hashlib
import io
import ipaddress
import socket
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import boto3
import httpx
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config import Settings
from app.services.malware import scan_bytes

_ALLOWED_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}


@dataclass(frozen=True, slots=True)
class StoredImage:
    storage_path: str
    public_url: str
    mime_type: str
    sha256: str
    width: int
    height: int


def _validated_remote_target(
    url: str, *, allowed_hosts: list[str] | None = None
) -> tuple[str, str, str]:
    """Resolve once and return an IP-pinned URL, Host header and TLS SNI name.

    The socket opened by httpx therefore uses exactly an address checked below;
    a second DNS answer cannot redirect the request to an internal service.
    """
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=422, detail="Only public HTTP(S) image URLs are allowed")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Credential-bearing URLs are not allowed")
    hostname = parsed.hostname.rstrip(".").lower()
    normalized_allowlist = {item.strip().rstrip(".").lower() for item in (allowed_hosts or []) if item.strip()}
    if normalized_allowlist and hostname not in normalized_allowlist:
        raise HTTPException(status_code=422, detail="Image host is not in the configured allowlist")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM
            )
        }
    except socket.gaierror as exc:
        raise HTTPException(status_code=422, detail="Image host could not be resolved") from exc
    vetted: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for raw_address in addresses:
        address = ipaddress.ip_address(raw_address)
        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        ):
            raise HTTPException(status_code=422, detail="Private or local image hosts are blocked")
        vetted.append(address)
    if not vetted:
        raise HTTPException(status_code=422, detail="Image host did not resolve to a public address")
    selected = sorted(vetted, key=lambda item: (item.version, int(item)))[0]
    ip_literal = f"[{selected}]" if selected.version == 6 else str(selected)
    pinned_netloc = f"{ip_literal}:{parsed.port}" if parsed.port else ip_literal
    host_header = hostname
    if parsed.port and parsed.port != (443 if parsed.scheme == "https" else 80):
        host_header = f"{hostname}:{parsed.port}"
    pinned_url = urlunsplit((parsed.scheme, pinned_netloc, parsed.path or "/", parsed.query, ""))
    return pinned_url, host_header, hostname


def _inspect_image(content: bytes) -> tuple[str, str, int, int]:
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            image_format = (image.format or "").upper()
            width, height = image.size
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=422, detail="The supplied file is not a valid image"
        ) from exc
    if image_format not in _ALLOWED_FORMATS:
        raise HTTPException(status_code=422, detail="Only JPEG, PNG and WEBP images are accepted")
    if width < 240 or height < 180:
        raise HTTPException(
            status_code=422, detail="Product images must be at least 240×180 pixels"
        )
    if width > 12000 or height > 12000:
        raise HTTPException(status_code=422, detail="Image dimensions exceed the safety limit")
    mime_type, extension = _ALLOWED_FORMATS[image_format]
    return mime_type, extension, width, height


def _store_bytes(*, content: bytes, product_id: str, settings: Settings) -> StoredImage:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if not content:
        raise HTTPException(status_code=422, detail="The image file is empty")
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Images may not exceed {settings.max_upload_mb} MB",
        )
    scan_bytes(content, settings=settings)
    mime_type, extension, width, height = _inspect_image(content)
    digest = hashlib.sha256(content).hexdigest()
    relative_path = Path("products") / product_id / f"{digest}{extension}"
    object_key = relative_path.as_posix()
    public_base = settings.public_media_base_url.rstrip("/")
    if settings.media_backend.lower() == "s3":
        if (
            not settings.s3_endpoint_url
            or not settings.s3_access_key_id
            or not settings.s3_secret_access_key
        ):
            raise HTTPException(
                status_code=503, detail="S3 media backend is not completely configured"
            )
        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_access_key.get_secret_value(),
        )
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=object_key,
            Body=content,
            ContentType=mime_type,
            Metadata={"sha256": digest},
        )
    else:
        absolute_path = settings.media_root / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        if not absolute_path.exists():
            temporary_path = absolute_path.with_suffix(absolute_path.suffix + ".tmp")
            temporary_path.write_bytes(content)
            temporary_path.replace(absolute_path)
    return StoredImage(
        storage_path=object_key,
        public_url=f"{public_base}/{object_key}",
        mime_type=mime_type,
        sha256=digest,
        width=width,
        height=height,
    )


async def store_upload(*, upload: UploadFile, product_id: str, settings: Settings) -> StoredImage:
    content = await upload.read(settings.max_upload_mb * 1024 * 1024 + 1)
    await upload.close()
    return _store_bytes(content=content, product_id=product_id, settings=settings)


async def import_remote_image(*, url: str, product_id: str, settings: Settings) -> StoredImage:
    pinned_url, host_header, sni_hostname = _validated_remote_target(
        url, allowed_hosts=settings.remote_image_allowed_hosts
    )
    max_bytes = settings.max_upload_mb * 1024 * 1024
    timeout = httpx.Timeout(12.0, connect=5.0)
    headers = {"User-Agent": "SmartDiag504-MediaImporter/0.4"}
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            headers=headers,
        ) as client:
            async with client.stream(
                "GET",
                pinned_url,
                headers={"Host": host_header},
                extensions={"sni_hostname": sni_hostname},
            ) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Image server returned HTTP {response.status_code}",
                    )
                content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                if content_type and content_type not in {"image/jpeg", "image/png", "image/webp"}:
                    raise HTTPException(
                        status_code=422, detail="Remote URL did not return an accepted image"
                    )
                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Remote images may not exceed {settings.max_upload_mb} MB",
                        )
                    chunks.append(chunk)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=422, detail="Remote image could not be downloaded") from exc
    return _store_bytes(content=b"".join(chunks), product_id=product_id, settings=settings)


def delete_stored_image(*, storage_path: str, settings: Settings) -> None:
    if settings.media_backend.lower() == "s3":
        if (
            not settings.s3_endpoint_url
            or not settings.s3_access_key_id
            or not settings.s3_secret_access_key
        ):
            raise HTTPException(
                status_code=503, detail="S3 media backend is not completely configured"
            )
        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_access_key.get_secret_value(),
        )
        client.delete_object(Bucket=settings.s3_bucket, Key=storage_path)
        return
    relative = Path(storage_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise HTTPException(status_code=422, detail="Invalid stored media path")
    absolute = settings.media_root / relative
    absolute.unlink(missing_ok=True)
    parent = absolute.parent
    if parent != settings.media_root:
        try:
            parent.rmdir()
        except OSError:
            pass


def _private_s3_client(settings: Settings):
    if (
        not settings.s3_endpoint_url
        or not settings.s3_access_key_id
        or not settings.s3_secret_access_key
    ):
        raise HTTPException(status_code=503, detail="El almacenamiento privado S3 no está configurado")
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id.get_secret_value(),
        aws_secret_access_key=settings.s3_secret_access_key.get_secret_value(),
    )


def store_private_evidence(
    *, content: bytes, object_key: str, mime_type: str, sha256: str, settings: Settings
) -> None:
    """Store one non-public OT object; access remains mediated by the authenticated API."""
    if not _valid_private_object_key(object_key):
        raise HTTPException(status_code=422, detail="Clave de evidencia privada inválida")
    scan_bytes(content, settings=settings)
    _private_s3_client(settings).put_object(
        Bucket=settings.s3_bucket,
        Key=object_key,
        Body=content,
        ContentType=mime_type,
        Metadata={"sha256": sha256},
    )


def read_private_evidence(*, object_key: str, settings: Settings) -> bytes:
    if not _valid_private_object_key(object_key):
        raise HTTPException(status_code=404, detail="Archivo de evidencia no disponible")
    try:
        response = _private_s3_client(settings).get_object(
            Bucket=settings.s3_bucket, Key=object_key
        )
        content = response["Body"].read(settings.max_upload_mb * 1024 * 1024 + 1)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Archivo de evidencia no disponible") from exc
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="La evidencia almacenada supera el límite")
    return content


def _valid_private_object_key(object_key: str) -> bool:
    """Allow only the private namespaces mediated by authenticated API routes."""
    parts = Path(object_key).parts
    return (
        bool(parts)
        and parts[0] in {"evidence", "payment-proofs"}
        and ".." not in parts
        and not Path(object_key).is_absolute()
    )

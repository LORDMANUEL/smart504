from fastapi import HTTPException
import pytest

from app.services import media
from app.services import malware
from app.config import Settings


def test_remote_image_target_is_pinned_to_vetted_address(monkeypatch) -> None:
    monkeypatch.setattr(
        media.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    pinned, host, sni = media._validated_remote_target(
        "https://images.example.test/catalog/part.png?size=large",
        allowed_hosts=["images.example.test"],
    )
    assert pinned == "https://93.184.216.34/catalog/part.png?size=large"
    assert host == "images.example.test"
    assert sni == "images.example.test"


def test_remote_image_rejects_unlisted_or_private_hosts(monkeypatch) -> None:
    with pytest.raises(HTTPException, match="allowlist"):
        media._validated_remote_target(
            "https://untrusted.example.test/image.png",
            allowed_hosts=["images.example.test"],
        )

    monkeypatch.setattr(
        media.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(2, 1, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(HTTPException, match="Private or local"):
        media._validated_remote_target("https://images.example.test/image.png")


def test_private_evidence_uses_non_public_s3_object(monkeypatch) -> None:
    objects: dict[str, bytes] = {}

    class Body:
        def __init__(self, content: bytes) -> None:
            self.content = content

        def read(self, _limit: int) -> bytes:
            return self.content

    class FakeS3:
        def put_object(self, **kwargs) -> None:
            assert kwargs["Bucket"] == "private-test"
            objects[kwargs["Key"]] = kwargs["Body"]

        def get_object(self, **kwargs):
            return {"Body": Body(objects[kwargs["Key"]])}

    monkeypatch.setattr(media.boto3, "client", lambda *_args, **_kwargs: FakeS3())
    settings = Settings(
        s3_endpoint_url="http://garage:3900",
        s3_bucket="private-test",
        s3_access_key_id="access",
        s3_secret_access_key="secret",
    )
    key = "evidence/SMARTDIAG504/ot-1/photo.jpg"
    media.store_private_evidence(
        content=b"private-photo",
        object_key=key,
        mime_type="image/jpeg",
        sha256="digest",
        settings=settings,
    )
    assert objects == {key: b"private-photo"}
    assert media.read_private_evidence(object_key=key, settings=settings) == b"private-photo"

    with pytest.raises(HTTPException, match="inválida"):
        media.store_private_evidence(
            content=b"x",
            object_key="../public/photo.jpg",
            mime_type="image/jpeg",
            sha256="digest",
            settings=settings,
        )


def test_malware_scanner_fails_closed_when_required(monkeypatch) -> None:
    def unavailable(*_args, **_kwargs):
        raise OSError("scanner unavailable")

    monkeypatch.setattr(malware.socket, "create_connection", unavailable)
    with pytest.raises(HTTPException, match="no disponible"):
        malware.scan_bytes(
            b"safe-looking-content",
            settings=Settings(malware_scanner_host="clamav", malware_scanner_required=True),
        )

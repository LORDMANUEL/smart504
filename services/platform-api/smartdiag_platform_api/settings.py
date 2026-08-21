from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    webhook_secret: str
    internal_api_key: str
    frappe_base_url: str
    frappe_api_key: str
    frappe_api_secret: str
    database_url: str
    redis_url: str
    s3_endpoint: str
    s3_region: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str
    allowed_origins: tuple[str, ...]

    @classmethod
    def from_env(cls, *, testing: bool = False) -> "Settings":
        origins = os.getenv(
            "ALLOWED_ORIGINS",
            "https://smartdiag504.com,https://clientes.smartdiag504.com,https://app.smartdiag504.com",
        )
        return cls(
            environment="test" if testing else os.getenv("ENVIRONMENT", "development"),
            webhook_secret="test-webhook-secret" if testing else os.getenv("WEBHOOK_SECRET", ""),
            internal_api_key=os.getenv("INTERNAL_API_KEY", ""),
            frappe_base_url=os.getenv("FRAPPE_BASE_URL", "http://frappe-frontend"),
            frappe_api_key=os.getenv("FRAPPE_API_KEY", ""),
            frappe_api_secret=os.getenv("FRAPPE_API_SECRET", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            redis_url=os.getenv("REDIS_URL", ""),
            s3_endpoint=os.getenv("S3_ENDPOINT", "http://garage:3900"),
            s3_region=os.getenv("S3_REGION", "garage"),
            s3_access_key=os.getenv("S3_ACCESS_KEY", ""),
            s3_secret_key=os.getenv("S3_SECRET_KEY", ""),
            s3_bucket=os.getenv("S3_BUCKET", "smartdiag-evidence"),
            allowed_origins=tuple(origin.strip() for origin in origins.split(",") if origin.strip()),
        )

    def adapter_checks(self) -> dict[str, str]:
        checks = {
            "database": bool(self.database_url),
            "cache": bool(self.redis_url),
            "object_storage": all(
                (
                    self.s3_endpoint,
                    self.s3_region,
                    self.s3_access_key,
                    self.s3_secret_key,
                    self.s3_bucket,
                )
            ),
            "frappe": all((self.frappe_base_url, self.frappe_api_key, self.frappe_api_secret)),
            "security": all((self.webhook_secret, self.internal_api_key)),
        }
        return {name: "configured" if configured else "not_configured" for name, configured in checks.items()}

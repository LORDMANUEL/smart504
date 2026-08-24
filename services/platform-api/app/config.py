from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SmartDiag504 Platform API"
    app_version: str = "0.4.0"
    environment: str = "development"
    database_url: str = "sqlite:///./smartdiag504.db"
    redis_url: str | None = None
    expected_schema_revision: str | None = None
    media_root: Path = Path("./var/media")
    private_evidence_root: Path = Path("./var/private/evidence")
    public_media_base_url: str = "/media"
    media_backend: str = "filesystem"
    private_evidence_backend: str = "filesystem"
    s3_endpoint_url: str | None = None
    s3_bucket: str = "smartdiag-media"
    s3_region: str = "us-east-1"
    s3_access_key_id: SecretStr | None = None
    s3_secret_access_key: SecretStr | None = None
    admin_api_token: SecretStr = SecretStr("change-me-before-production")
    recovery_token_enabled: bool = False
    recovery_token_allowed_cidrs: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["127.0.0.1/32", "::1/128"])
    staff_auth_secret: SecretStr | None = None
    client_auth_secret: SecretStr | None = None
    staff_session_hours: int = Field(default=8, ge=1, le=24)
    staff_login_max_attempts: int = Field(default=5, ge=3, le=20)
    staff_login_lock_minutes: int = Field(default=15, ge=1, le=1440)
    cashier_access_code: SecretStr | None = None
    event_hmac_secret: SecretStr = SecretStr("change-event-secret")
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    google_cse_api_key: SecretStr | None = None
    google_cse_id: str | None = None
    max_upload_mb: int = 8
    remote_image_allowed_hosts: Annotated[list[str], NoDecode] = Field(default_factory=list)
    campaign_max_upload_mb: int = 25
    malware_scanner_host: str | None = None
    malware_scanner_port: int = Field(default=3310, ge=1, le=65535)
    malware_scanner_required: bool = False
    malware_scanner_timeout_seconds: float = Field(default=10.0, ge=1.0, le=60.0)
    node_id: str = "node-local"
    node_role: str = "api"
    lease_ttl_seconds: int = 30
    frappe_base_url: str | None = None
    frappe_required: bool = True
    frappe_api_key: SecretStr | None = None
    frappe_api_secret: SecretStr | None = None
    frappe_price_list: str = "Standard Selling"
    frappe_company: str = "SmartDiag504 Demo"
    frappe_customer: str = "Consumidor Final SmartDiag504"
    frappe_warehouse_suffix: str = "SD504"
    frappe_tax_account: str | None = None
    invoice_verification_mode: str = "strict"
    forwarded_allow_ips: str = "127.0.0.1"
    owner_approval_email: str = "admin@smartdiag504.com"
    approval_public_base_url: str = "https://taller.nexusmedi.org"
    approval_expiry_hours: int = Field(default=24, ge=1, le=168)
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_use_tls: bool = True
    smtp_from_email: str = "notificaciones@smartdiag504.com"
    external_backup_configured: bool = False
    local_backup_configured: bool = False
    local_restore_tested: bool = False
    fiscal_hardware_certified: bool = False
    offsite_restore_tested: bool = False
    whatsapp_webhook_url: str | None = None
    whatsapp_webhook_token: SecretStr | None = None
    sms_webhook_url: str | None = None
    sms_webhook_token: SecretStr | None = None
    push_webhook_url: str | None = None
    push_webhook_token: SecretStr | None = None

    # Public chatbot. The browser only receives a short-lived opaque session token.
    public_chat_enabled: bool = True
    chat_session_secret: SecretStr = SecretStr("change-chat-session-secret")
    ai_gateway_url: str = "http://haproxy:8083"
    ai_gateway_internal_token: SecretStr = SecretStr("change-ai-gateway-token")
    ai_gateway_timeout_seconds: float = Field(default=25.0, ge=1.0, le=120.0)
    chatbot_session_ttl_minutes: int = Field(default=1440, ge=15, le=10080)
    chatbot_history_limit: int = Field(default=12, ge=2, le=30)
    chatbot_rate_limit_messages: int = Field(default=30, ge=2, le=300)
    chatbot_rate_window_seconds: int = Field(default=3600, ge=60, le=86400)
    public_booking_limit_per_minute: int = Field(default=5, ge=1, le=100)
    public_order_limit_per_minute: int = Field(default=8, ge=1, le=100)
    public_lead_limit_per_minute: int = Field(default=5, ge=1, le=100)
    public_client_registration_limit_per_minute: int = Field(default=3, ge=1, le=30)
    managed_mail_domain: str = "smartdiag504.com"
    managed_mailbox_enabled: bool = False
    frappe_social_login_enabled: bool = False
    public_chat_session_limit_per_minute: int = Field(default=6, ge=1, le=100)
    public_chat_message_limit_per_minute: int = Field(default=12, ge=1, le=100)
    trusted_cdn_cidrs: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
            "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20",
            "197.234.240.0/22", "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
            "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22",
            "2400:cb00::/32", "2606:4700::/32", "2803:f800::/32", "2405:b500::/32",
            "2405:8100::/32", "2a06:98c0::/29", "2c0f:f248::/32",
        ]
    )
    client_demo_email: str = "cliente.demo@smartdiag504.invalid"
    client_demo_password: SecretStr = SecretStr("change-client-demo-password")
    seed_demo_data: bool = False
    client_session_ttl_minutes: int = Field(default=480, ge=15, le=1440)
    chatbot_welcome_message: str = (
        "Hola, soy el asistente de SmartDiag504. Puedo orientarle sobre servicios, reservas, "
        "repuestos y el proceso de su vehículo. No sustituyo una inspección técnica."
    )
    chatbot_privacy_notice: str = (
        "Al continuar acepta que la conversación se guarde temporalmente para atender su consulta. "
        "No comparta contraseñas, tarjetas ni datos bancarios."
    )
    chatbot_quick_prompts: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "Reservar diagnóstico",
            "Buscar repuesto",
            "Consultar servicios",
            "Contactar por WhatsApp",
        ]
    )
    chatbot_quick_action_codes: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["BOOK_SERVICE", "SEARCH_PARTS", "CONTACT_WHATSAPP"]
    )

    business_name: str = "SmartDiag504"
    business_phone: str = "+504 0000-0000"
    business_whatsapp_url: str = "https://wa.me/50400000000"
    business_address: str = "San Pedro Sula, Honduras"
    business_hours: str = "Horario sujeto a confirmación"

    @field_validator(
        "cors_origins",
        "chatbot_quick_prompts",
        "chatbot_quick_action_codes",
        "remote_image_allowed_hosts",
        "trusted_cdn_cidrs",
        "recovery_token_allowed_cidrs",
        mode="before",
    )
    @classmethod
    def parse_list(cls, value: object) -> object:
        if isinstance(value, str):
            separator = "|" if "|" in value else ","
            return [item.strip() for item in value.split(separator) if item.strip()]
        return value

    @field_validator("media_root", mode="before")
    @classmethod
    def normalize_media_root(cls, value: object) -> Path:
        return Path(str(value)).expanduser()

    @field_validator("ai_gateway_url", mode="before")
    @classmethod
    def normalize_ai_gateway_url(cls, value: object) -> str:
        return str(value).rstrip("/")

    @property
    def chatbot_max_history_messages(self) -> int:
        return self.chatbot_history_limit

    @property
    def chat_max_messages_per_hour(self) -> int:
        return self.chatbot_rate_limit_messages

    @property
    def public_phone(self) -> str:
        return self.business_phone

    @property
    def public_location(self) -> str:
        return self.business_address

    @property
    def production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def staff_signing_secret(self) -> str:
        configured = self.staff_auth_secret or self.chat_session_secret
        return configured.get_secret_value()

    @property
    def client_signing_secret(self) -> str:
        configured = self.client_auth_secret or self.staff_auth_secret or self.chat_session_secret
        return configured.get_secret_value()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

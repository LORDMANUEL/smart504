from __future__ import annotations

import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import NotificationDelivery, SocialMessage
from app.request_context import current_identity, worker_identity


def enqueue_notification(
    db: Session,
    *,
    channel: str,
    recipient: str,
    subject: str | None,
    body_text: str,
    template_key: str,
    aggregate_type: str,
    aggregate_id: str,
    idempotency_key: str,
    payload: dict[str, object] | None = None,
) -> NotificationDelivery:
    identity = current_identity()
    existing = db.scalar(
        select(NotificationDelivery).where(
            NotificationDelivery.organization_id == identity.organization_id,
            NotificationDelivery.idempotency_key == idempotency_key,
        )
    )
    if existing:
        return existing
    delivery = NotificationDelivery(
        organization_id=identity.organization_id,
        channel=channel.upper(),
        recipient=recipient.strip(),
        subject=subject,
        body_text=body_text,
        template_key=template_key,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        idempotency_key=idempotency_key,
        payload_json=payload or {},
    )
    db.add(delivery)
    return delivery


def _send_email(delivery: NotificationDelivery, settings: Settings) -> str:
    if not settings.smtp_host:
        raise RuntimeError("SMTP no configurado")
    message = EmailMessage()
    message["Subject"] = delivery.subject or "Notificacion SmartDiag504"
    message["From"] = settings.smtp_from_email
    message["To"] = delivery.recipient
    message.set_content(delivery.body_text)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
        if settings.smtp_use_tls:
            client.starttls()
        if settings.smtp_username and settings.smtp_password:
            client.login(settings.smtp_username, settings.smtp_password.get_secret_value())
        client.send_message(message)
    return message.get("Message-ID") or f"smtp:{delivery.id}"


def _send_webhook(delivery: NotificationDelivery, url: str | None, token) -> str:
    if not url:
        raise RuntimeError(f"Proveedor {delivery.channel} no configurado")
    headers = {"Idempotency-Key": delivery.idempotency_key}
    if token:
        headers["Authorization"] = f"Bearer {token.get_secret_value()}"
    response = httpx.post(
        url,
        headers=headers,
        json={
            "recipient": delivery.recipient,
            "message": delivery.body_text,
            "template": delivery.template_key,
            "metadata": delivery.payload_json,
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json() if response.content else {}
    return str(payload.get("id") or payload.get("message_id") or f"webhook:{delivery.id}")


def deliver_notifications(db: Session, settings: Settings, *, limit: int = 50) -> dict[str, int]:
    now = datetime.now(UTC)
    deliveries = list(
        db.scalars(
            select(NotificationDelivery)
            .where(NotificationDelivery.status.in_(("PENDING", "FAILED")), NotificationDelivery.scheduled_at <= now)
            .order_by(NotificationDelivery.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
            .execution_options(include_all_tenants=True)
        )
    )
    result = {"selected": len(deliveries), "sent": 0, "failed": 0, "blocked": 0}
    for delivery in deliveries:
        with worker_identity(actor="notification-worker", organization_id=delivery.organization_id):
            delivery.attempts += 1
            try:
                if delivery.channel == "EMAIL":
                    reference = _send_email(delivery, settings)
                elif delivery.channel == "WHATSAPP":
                    reference = _send_webhook(delivery, settings.whatsapp_webhook_url, settings.whatsapp_webhook_token)
                elif delivery.channel == "SMS":
                    reference = _send_webhook(delivery, settings.sms_webhook_url, settings.sms_webhook_token)
                elif delivery.channel == "PUSH":
                    reference = _send_webhook(delivery, settings.push_webhook_url, settings.push_webhook_token)
                else:
                    raise RuntimeError("Canal de notificacion no soportado")
                delivery.status = "SENT"
                delivery.provider_reference = reference
                delivery.last_error = None
                delivery.sent_at = now
                if delivery.aggregate_type == "SOCIAL_MESSAGE":
                    social_message = db.get(SocialMessage, delivery.aggregate_id)
                    if social_message:
                        social_message.status = "SENT"
                        social_message.provider_reference = reference
                result["sent"] += 1
            except Exception as exc:
                delivery.last_error = str(exc)[:500]
                if "no configurado" in delivery.last_error:
                    delivery.status = "BLOCKED"
                    result["blocked"] += 1
                else:
                    delivery.status = "FAILED"
                    result["failed"] += 1
                if delivery.aggregate_type == "SOCIAL_MESSAGE":
                    social_message = db.get(SocialMessage, delivery.aggregate_id)
                    if social_message:
                        social_message.status = delivery.status
            db.commit()
    return result

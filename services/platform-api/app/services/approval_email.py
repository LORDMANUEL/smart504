from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.config import Settings


def send_approval_email(
    *, settings: Settings, recipient: str, request_type: str, reference: str, reason: str, approval_url: str
) -> tuple[str, str | None]:
    """Send the owner link when SMTP exists, otherwise preserve an explicit pending state."""
    if not settings.smtp_host:
        return "PENDING_EMAIL_CONFIGURATION", "Configure SMTP_HOST y las credenciales de correo saliente"
    message = EmailMessage()
    label = "devolucion" if request_type == "RETURN" else "garantia"
    message["Subject"] = f"SmartDiag504: autorizar {label} {reference}"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(
        f"Se solicito una {label} para {reference}.\n\nMotivo: {reason}\n\n"
        f"Revise y decida en este enlace de un solo uso:\n{approval_url}\n\n"
        "El enlace vence automaticamente. No comparta este mensaje."
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
            if settings.smtp_use_tls:
                client.starttls()
            if settings.smtp_username and settings.smtp_password:
                client.login(settings.smtp_username, settings.smtp_password.get_secret_value())
            client.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        return "DELIVERY_FAILED", str(exc)[:500]
    return "SENT", None
